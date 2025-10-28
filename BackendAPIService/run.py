from app import app

if __name__ == "__main__":
    # Bind to 0.0.0.0 for containerized environments and run on port 3001
    app.run(host="0.0.0.0", port=3001, debug=False)
