# app package
@app.get("/api/v1/health")
async def health():
    fraud_status = "running" if hasattr(app.state, 'fraud_detector') and app.state.fraud_detector else "disabled"
    return {
        "status": "ok",
        "fraud_detection": fraud_status,  # ADD THIS
        "mock_mode": settings.use_mock_apis
    }
