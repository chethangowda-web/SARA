import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyDu-DLuHv5cur2dANWxOn1OIx-Ojogex-A",
  authDomain: "sara-e3a50.firebaseapp.com",
  projectId: "sara-e3a50",
  storageBucket: "sara-e3a50.firebasestorage.app",
  messagingSenderId: "393997185127",
  appId: "1:393997185127:web:e45d69b56fd6bd2228e4c2",
  measurementId: "G-X5QV10X2ZG"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Auth
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
