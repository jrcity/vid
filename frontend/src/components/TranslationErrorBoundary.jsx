import React from 'react';

class TranslationErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Translation system error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      // Fallback UI with English only
      return (
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <h2>Language System Error</h2>
          <p>Please refresh the page. Using English fallback.</p>
          <button onClick={() => window.location.reload()}>
            Refresh Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default TranslationErrorBoundary;
