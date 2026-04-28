import React, { useEffect, useState } from 'react';
import styles from './CatalystLogin.module.css';

const CatalystLogin = ({ onSuccess, onError }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadCatalystScripts = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Load the main Catalyst SDK script
        const catalystSDK = document.createElement('script');
        catalystSDK.src = 'https://static.zohocdn.com/catalyst/sdk/js/4.5.0/catalystWebSDK.js';
        catalystSDK.async = true;

        catalystSDK.onload = () => {
          console.log('✓ Catalyst SDK loaded successfully');

          // Once SDK is loaded, load the init script
          const initScript = document.createElement('script');
          initScript.src = '/__catalyst/sdk/init.js';
          initScript.async = true;

          initScript.onload = () => {
            console.log('✓ Catalyst init script loaded successfully');

            // Initialize the embedded login
            if (window.catalyst && window.catalyst.auth) {
              const config = {};
              /* config is optional - you can customize:
              {
                css_url: "/css/embeddediframe.css", // Provide your custom CSS file path here. If no path is provided default css will be rendered
                service_url: "/app/index.html", // This value is optional. You can provide your redirect URL here.
                is_customize_forgot_password: true, // Default value is false. Keep this value as true, if you wish to customize Forgot Password page
                forgot_password_id: "forgotPasswordDivElementId", // The Element id in which forgot password page should be loaded,If no value is provided, it will be rendered in the "loginDivElementId" by default
                forgot_password_css_url: "/css/forgotPwd.css" // Provide your custom CSS file path for the Forgot Password page.If no path is provided,then the default CSS will be rendered.
              }
              */

              try {
                window.catalyst.auth.signIn("loginDivElementId", config);
                console.log('✓ Catalyst signIn initialized');
                setIsLoading(false);

                // Optional: Listen for authentication success events
                // This may need to be adjusted based on Catalyst's actual event system
                window.addEventListener('message', (event) => {
                  if (event.data && event.data.type === 'LOGIN_SUCCESS') {
                    onSuccess && onSuccess();
                  }
                });

              } catch (initError) {
                console.error('✗ Error initializing Catalyst signIn:', initError);
                setError('Failed to initialize authentication: ' + initError.message);
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
          };

          initScript.onerror = (e) => {
            const errMsg = 'Failed to load Catalyst initialization script. Make sure Catalyst is running on localhost:4800';
            console.error('✗ ' + errMsg, e);
            setError(errMsg);
            setIsLoading(false);
            onError && onError(new Error(errMsg));
          };

          document.head.appendChild(initScript);
        };

        catalystSDK.onerror = (e) => {
          const errMsg = 'Failed to load Catalyst SDK from CDN';
          console.error('✗ ' + errMsg, e);
          setError(errMsg);
          setIsLoading(false);
          onError && onError(new Error(errMsg));
        };

        document.head.appendChild(catalystSDK);

      } catch (loadError) {
        console.error('✗ Unexpected error loading Catalyst scripts:', loadError);
        setError('Unexpected error: ' + loadError.message);
        setIsLoading(false);
        onError && onError(loadError);
      }
    };

    loadCatalystScripts();

    // Cleanup function
    return () => {
      // Remove scripts when component unmounts
      const catalystScripts = document.querySelectorAll('script[src*="catalyst"], script[src*="zohocdn"]');
      catalystScripts.forEach(script => {
        if (script.parentNode) {
          script.parentNode.removeChild(script);
        }
      });
    };
  }, [onSuccess, onError]);

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