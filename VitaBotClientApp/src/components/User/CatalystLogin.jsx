import React, { useEffect, useState } from 'react';
import styles from './CatalystLogin.module.css';
import { useCatalystSDK } from '../../hooks/useCatalystSDK';

const CatalystLogin = ({ onSuccess, onError }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const { isReady, error: sdkError } = useCatalystSDK();
  
  useEffect(() => {
    if (sdkError) {
      setError(sdkError);
      setIsLoading(false);
      onError && onError(new Error(sdkError));
      return;
    }

    if (!isReady) return;

    if (window.catalyst && window.catalyst.auth) {
      const config = {};
      try {
        let auth = window.catalyst.auth;
        auth.signIn('loginDivElementId', config);

        console.log('✓ Catalyst signIn initialized', auth );
        setIsLoading(false);
      } catch (initError) {
        console.error('✗ Error initializing Catalyst signIn:', initError);
        const errMsg = 'Failed to initialize authentication: ' + initError.message;
        setError(errMsg);
        setIsLoading(false);
        onError && onError(initError);
      }
    } else {
      const errMsg = 'Catalyst authentication not available after loading scripts';
      console.error('✗ ' + errMsg);
      setError(errMsg);
      setIsLoading(false);
      onError && onError(new Error(errMsg));
    }
  }, [isReady, sdkError, onError]);

  useEffect(() => {
    const handleMessage = (event) => {
      if (event.data && event.data.type === 'LOGIN_SUCCESS') {
        onSuccess && onSuccess();
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [onSuccess]);

  return (
    <div className={styles.loginContainer}>
      {isLoading && (
        <div className={styles.loadingIndicator}>
          <div className={styles.loadingSpinner}>🔄</div>
          <div className={styles.loadingText}>Loading authentication...</div>
        </div>
      )}

      {error && (
        <div className={styles.errorMessage}>
          <span className={styles.errorTitle}>Authentication Error:</span>
          {error}
          <div className={styles.errorDescription}>
            Please ensure Catalyst is running on localhost:4800 and refresh the page.
          </div>
        </div>
      )}

      <div
        id="loginDivElementId"
        className={`${styles.loginContent} ${isLoading ? styles.loading : ''}`}
      >
        <h3 className={styles.loginTitle}>Iniciar Sesión</h3>
        {/* The Catalyst embedded login will be rendered here */}
      </div>
    </div>
  );
};

export default CatalystLogin;