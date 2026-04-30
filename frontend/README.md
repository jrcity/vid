# VID — Virtual ID · Pan-African Network Identity 🌍✨

The frontend for VID is a premium, mobile-first React application designed to provide a secure, private, and visually stunning digital identity experience for everyone across Africa. It leverages real-time mobile network signals to verify identity without relying on centralized, vulnerable databases.

## 🚀 Key Features

### 1. Multi-SIM Verification
*   **Smart Detection**: Efficiently detects the country and region for up to 3 SIM cards simultaneously.
*   **Real-time Feedback**: Debounced API calls ensure a smooth user experience while typing, providing instant flag and country validation.

### 2. Prestige "Gold Edition" Digital ID Card
*   **Metallic Aesthetic**: A radiant, metallic gold gradient design with high-end guilloche security patterns.
*   **Unified Branding**: Features a unique VID Emblem watermark and the project motto: *"Empowering African Digital Identity through Mobile Innovation"*.
*   **Dynamic Labels**: Automatically adapts to local naming conventions (e.g., "Virtual NIN" for Nigeria).
*   **Secure QR Code**: Integrated QR code for instant third-party verification.

### 3. Professional Sharing & Export
*   **PNG Generation**: High-fidelity client-side image generation using `html-to-image`.
*   **Native Sharing**: Integrated with the Web Share API for seamless sharing to WhatsApp, Telegram, or business platforms.

### 4. SEO & Privacy
*   **Dynamic Meta Tags**: Powered by `react-helmet-async` for optimized social previews and search engine discoverability.
*   **Privacy-by-Design**: No PII (Personally Identifiable Information) is stored in the browser; only masked data and verified hashes are handled.

## 🛠️ Technology Stack

*   **Framework**: [React 18](https://reactjs.org/) (TypeScript)
*   **Build Tool**: [Vite](https://vitejs.dev/)
*   **Styling**: [Tailwind CSS](https://tailwindcss.com/) with custom premium animations and native-feel components.
*   **State Management**: [TanStack Query (React Query) v5](https://tanstack.com/query/latest) for efficient, cached API orchestration.
*   **Icons**: [React Icons](https://react-icons.github.io/react-icons/) (Material Design)
*   **QR Generation**: [qrcode.react](https://github.com/zpao/qrcode.react)

## 📁 Project Structure

```text
src/
├── components/   # Reusable UI components (SEO, Navbar, etc.)
├── hooks/        # Custom React Query hooks for API communication
├── pages/        # Main application views (Enroll, Certificate, Verify)
├── services/     # API client configuration (Axios)
├── types/        # Comprehensive TypeScript interfaces
└── assets/       # Global styles and static assets
```

## 🛠️ Getting Started

1.  **Install Dependencies**:
    ```bash
    pnpm install
    ```

2.  **Environment Setup**:
    Create a `.env` file based on `.env.example`:
    ```env
    VITE_API_URL=http://localhost:8000
    ```

3.  **Development Mode**:
    ```bash
    npm run dev
    ```

4.  **Production Build**:
    ```bash
    npm run build
    ```

---
*Part of the VID Trust Network. Built for the African Digital Future.*
