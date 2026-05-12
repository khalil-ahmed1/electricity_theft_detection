import streamlit as st
import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
import plotly.express as px
import os

# Suppress TensorFlow logs for a clean UI
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# --- 1. SET PAGE CONFIG ---
st.set_page_config(page_title="Electricity Theft Detector (Hybrid)", layout="wide")

# --- 2. LOAD ASSETS ---
@st.cache_resource
def load_assets():
    # Load the two healthy separate models
    cnn_model = tf.keras.models.load_model('electricity_theft_model.keras')
    ae_model = tf.keras.models.load_model('autoencoder_model.keras')
    scaler = joblib.load('scaler.pkl')
    return cnn_model, ae_model, scaler

try:
    cnn_model, ae_model, scaler = load_assets()
except Exception as e:
    st.error(f"Error loading assets: {e}")
    st.info("Ensure 'electricity_theft_model.keras', 'autoencoder_model.keras', and 'scaler.pkl' are in this folder.")
    st.stop()

# --- 3. UI HEADER ---
st.title("⚡ Smart Grid: Electricity Theft Detection System")
st.markdown("Analyzing consumption patterns using a **Weighted Ensemble (CNN + Autoencoder)**.")

# --- 4. FILE UPLOADER ---
uploaded_file = st.file_uploader("Upload Consumer CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Auto-detect ID column
    possible_ids = ['CONS_NO', 'User', 'Consumer_ID', 'ID', 'User_ID']
    id_col = next((col for col in possible_ids if col in df.columns), df.columns[0])

    mode = st.sidebar.radio("Analysis Mode", ["Individual Investigation", "Bulk Detection Report"])

    # --- MODE 1: INDIVIDUAL INVESTIGATION ---
    if mode == "Individual Investigation":
        selected_id = st.selectbox(f"Select Consumer ({id_col})", df[id_col].unique())
        user_row = df[df[id_col] == selected_id].iloc[[0]] 
        
        numeric_data = user_row.select_dtypes(include=[np.number])
        for col in [id_col, 'FLAG', 'flag']:
            if col in numeric_data.columns:
                numeric_data = numeric_data.drop(columns=[col])

        if numeric_data.shape[1] >= 1034:
            numeric_data = numeric_data.iloc[:, :1034].fillna(0)
            scaled = scaler.transform(numeric_data.values).flatten() 
            
            # --- FEATURE ENGINEERING ---
            r_avg = np.nan_to_num(pd.Series(scaled).rolling(window=7, min_periods=1).mean().values)
            var = np.nan_to_num(pd.Series(scaled).rolling(window=7, min_periods=1).var().fillna(0).values)
            
            combined = np.column_stack((scaled, r_avg, var))
            X_input_cnn = combined.reshape(1, 1034, 3)
            X_input_ae = combined.reshape(1, -1) # Flattened for Autoencoder

            # 1. Get CNN Prediction
            cnn_prob = cnn_model.predict(X_input_cnn, verbose=0)[0][0]

            # 2. Get Autoencoder Anomaly Score (MSE)
            reconstruction = ae_model.predict(X_input_ae, verbose=0)
            mse = np.mean(np.power(X_input_ae - reconstruction, 2))
            # Normalize MSE to 0-1 (thresholded at 0.1 for SGCC dataset)
            ae_score = min(mse / 0.1, 1.0) 

            # 3. Final Hybrid Score (70% CNN, 30% AE)
            hybrid_prob = (cnn_prob * 0.7) + (ae_score * 0.3)

            # UI Output
            fig = px.line(y=scaled, title=f"Consumption Trend: {selected_id}", labels={'y':'Scaled Units','x':'Day'})
            st.plotly_chart(fig, use_container_width=True)

            col1, col2 = st.columns(2)
            if hybrid_prob > 0.2:
                col1.error("### 🚨 STATUS: THEFT DETECTED")
                st.warning(f"Detection Logic: CNN ({cnn_prob:.1%}) & Anomaly Score ({ae_score:.1%}) suggest high theft probability.")
            else:
                col1.success("### ✅ STATUS: NORMAL")
                st.info("Detection Logic: Pattern matches learned normality thresholds.")
            
            col2.metric("Ensemble Suspicion Score", f"{hybrid_prob:.2%}")
        else:
            st.error(f"❌ Error: Need 1034 days of data.")

    # --- MODE 2: BULK DETECTION REPORT ---
    elif mode == "Bulk Detection Report":
        if st.button("🚀 Run Full Ensemble Analysis"):
            numeric_df = df.select_dtypes(include=[np.number])
            for col in [id_col, 'FLAG', 'flag']:
                if col in numeric_df.columns:
                    numeric_df = numeric_df.drop(columns=[col])

            if numeric_df.shape[1] >= 1034:
                numeric_df = numeric_df.iloc[:, :1034].fillna(0)
                
                with st.spinner("Processing Weighted Ensemble..."):
                    all_scaled = scaler.transform(numeric_df.values)
                    
                    # Prepare CNN data
                    df_temp = pd.DataFrame(all_scaled)
                    all_r_avg = df_temp.rolling(window=7, axis=1, min_periods=1).mean().fillna(0).values
                    all_var = df_temp.rolling(window=7, axis=1, min_periods=1).var().fillna(0).values
                    X_bulk_cnn = np.stack((all_scaled, all_r_avg, all_var), axis=2)
                    
                    # Prepare AE data
                    X_bulk_ae = X_bulk_cnn.reshape(X_bulk_cnn.shape[0], -1)

                    # Predictions
                    cnn_probs = cnn_model.predict(X_bulk_cnn, verbose=0).flatten()
                    ae_reconstructions = ae_model.predict(X_bulk_ae, verbose=0)
                    ae_mses = np.mean(np.power(X_bulk_ae - ae_reconstructions, 2), axis=1)
                    ae_scores = np.minimum(ae_mses / 0.1, 1.0)

                    # Combine
                    final_probs = (cnn_probs * 0.7) + (ae_scores * 0.3)
                    results = ["Theft" if p > 0.2 else "Normal" for p in final_probs]

                    # Summary Metrics
                    st.divider()
                    st.subheader("📊 Grid-Wide Ensemble Report")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Analyzed", len(results))
                    m2.metric("Normal Users", results.count("Normal"))
                    m3.metric("Theft Cases", results.count("Theft"), delta_color="inverse")

                    report_df = pd.DataFrame({
                        id_col: df[id_col], 
                        "Status": results, 
                        "Hybrid Score": [f"{x:.2%}" for x in final_probs]
                    })
                    st.dataframe(report_df, use_container_width=True)
                    
                    # Download Section
                    st.subheader("📥 Download Section")
                    d_col1, d_col2 = st.columns(2)
                    d_col1.download_button("📂 Full CSV Report", data=report_df.to_csv(index=False), file_name="ensemble_report.csv", use_container_width=True)
                    theft_df = report_df[report_df["Status"] == "Theft"]
                    d_col2.download_button("🚨 Download Theft List", data=theft_df.to_csv(index=False), file_name="flagged_consumers.csv", use_container_width=True)

else:
    st.info("Please upload your SGCC data to begin the ensemble analysis.")
