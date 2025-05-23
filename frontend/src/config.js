const config = {
  api: {
    upload: process.env.VITE_BACKEND_URL || 'http://localhost:8001',
    status: process.env.VITE_STATUS_URL || 'http://localhost:8002'
  }
};

export default config;
