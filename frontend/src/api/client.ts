import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export const client = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export default client;
