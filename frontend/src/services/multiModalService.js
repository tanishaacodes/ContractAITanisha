import axios from 'axios';

const API_BASE_URL = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const getAuthHeaders = () => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`,
});

// Voice Contract: accepts audio file
export const uploadVoiceContract = async (audioFile) => {
  const formData = new FormData();
  formData.append('audio', audioFile);
  const response = await axios.post(
    `${API_BASE_URL}/api/multimodal/voice/`,
    formData,
    {
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
};

// Document Scanner: accepts image or PDF file
export const uploadDocument = async (docFile) => {
  const formData = new FormData();
  formData.append('document', docFile);
  const response = await axios.post(
    `${API_BASE_URL}/api/multimodal/document/`,
    formData,
    {
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
};

// Email Parser: accepts email text body
export const parseEmail = async (emailText) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/multimodal/email/`,
    { email_text: emailText },
    { headers: getAuthHeaders() }
  );
  return response.data;
};
