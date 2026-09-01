import api from './api';

/**
 * Uploads a face image sample for a student.
 * @param {string} studentId
 * @param {Blob|File} imageBlob
 */
export const registerFace = async (studentId, imageBlob) => {
  const formData = new FormData();
  formData.append('student_id', studentId);
  formData.append('file', imageBlob, 'face_sample.jpg');

  const response = await api.post('/face/register', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * Sends a camera image frame to backend for face recognition.
 * @param {Blob|File} imageBlob
 */
export const recognizeFace = async (imageBlob) => {
  const formData = new FormData();
  formData.append('file', imageBlob, 'frame.jpg');

  const response = await api.post('/face/recognize', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * Retrieves safe face registration status for a student.
 * @param {string} studentId
 */
export const getFaceStatus = async (studentId) => {
  const response = await api.get(`/face/student/${studentId}`);
  return response.data;
};

/**
 * Admin-only deactivation of face embeddings for a student.
 * @param {string} studentId
 */
export const deleteFace = async (studentId) => {
  const response = await api.delete(`/face/student/${studentId}`);
  return response.data;
};
