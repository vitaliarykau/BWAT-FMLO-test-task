import React, { useState } from 'react';
import {
  Box,
  Button,
  Container,
  Paper,
  Typography,
  TextField,
  CircularProgress,
} from '@mui/material';
import axios from 'axios';
import config from '../config';

function UploadPage() {
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsLoading(true);
    setMessage('');

    if (!file) {
      setMessage('Please select a file first');
      setIsLoading(false);
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', file);

      await axios.post(`${config.api.upload}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setMessage('File uploaded successfully!');
      setFile(null);
    } catch (error) {
      setMessage('Error uploading file: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Paper sx={{ p: 4, mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Upload PDF
        </Typography>
        
        <form onSubmit={handleSubmit}>
          <Box sx={{ mb: 3 }}>
            <TextField
              fullWidth
              type="file"
              onChange={handleFileChange}
              disabled={isLoading}
              accept=".pdf"
              helperText="Please upload a PDF file"
            />
          </Box>
          
          <Button
            variant="contained"
            color="primary"
            type="submit"
            disabled={isLoading || !file}
            fullWidth
            sx={{ mb: 2 }}
          >
            {isLoading ? <CircularProgress size={24} /> : 'Upload'}
          </Button>

          {message && (
            <Typography color={message.includes('Error') ? 'error' : 'success'}>
              {message}
            </Typography>
          )}
        </form>
      </Paper>
    </Container>
  );
}

export default UploadPage;
