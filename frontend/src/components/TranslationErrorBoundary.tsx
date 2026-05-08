import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

/**
 * Error boundary to prevent translation errors from crashing the UI
 */
class TranslationErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(_: Error): State {
    return { hasError: true };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Translation Error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 text-center">
          <p className="text-sm text-slate-500 italic">Something went wrong loading translations.</p>
          <button 
            onClick={() => this.setState({ hasError: false })}
            className="text-xs text-brand-accent underline mt-2"
          >
            Retry
          </button>
        </div>
      );
    }

    return this.children;
  }

  // Helper for class component children access
  private get children() {
    return this.props.children;
  }
}

export default TranslationErrorBoundary;
