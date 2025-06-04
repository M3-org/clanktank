const { launch, getStream, wss } = require('puppeteer-stream');
const path = require('path');
const fs = require('fs');
const os = require('os');

/**
 * Improved class to automate playback of Shmotime episodes with video and audio recording
 * using puppeteer-stream for native browser audio/video capture
 */
class ShmotimePlayer {
  /**
   * Create a new ShmotimePlayer instance
   * @param {Object} options Configuration options
   */
  constructor(options = {}) {
    this.options = {
      headless: false, // Run in non-headless mode for better audio support
      record: true,
      verbose: true,
      outputDir: './recordings',
      waitTimeout: 60000, // 60 seconds
      navigationTimeout: 5000, // 5 seconds to wait for navigation after episode end
      outputFormat: 'mp4', // MP4 or WebM format (puppeteer-stream supports both natively)
      // Video resolution settings
      videoWidth: 1920,
      videoHeight: 1080,
      frameRate: 30,
      ...options
    };

    this.browser = null;
    this.page = null;
    this.stream = null;
    this.outputFile = null;
    this.episodeInfo = null;
    this.navigationMonitor = null;
    this.endDetected = false;
  }

   /**
   * Load a Shmotime episode URL
   * @param {string} url The URL of the episode to play
   */
  async loadEpisodeUrl(url) {
    this.log(`Loading episode: ${url}`);

    try {
      // Monitor page for navigations to detect episode end
      this.startNavigationMonitoring(url);

      // Navigate to the episode page
      await this.page.goto(url, {
        waitUntil: 'networkidle2',
        timeout: this.options.waitTimeout
      });

      // Get episode info for filename
      this.episodeInfo = await this.page.evaluate(() => {
        return {
          title: document.title.split(' - ')[0] || 'episode',
          showTitle: window.shmotimeVoice?.showTitle || 'show',
          episodeId: window.shmotimeVoice?.shmotimeId || ''
        };
      });

      // Set up event interceptors to detect episode completion
      await this.page.evaluate(() => {
        // Listen for navigation changes
        const originalPushState = history.pushState;
        history.pushState = function() {
          originalPushState.apply(this, arguments);
          console.log(`Navigation detected to: ${arguments[2]}`);
        };

        // Listen for navigation events
        window.addEventListener('beforeunload', function() {
          console.log('Page navigation or unload detected');
        });

        // Ensure audio isn't muted
        document.querySelectorAll('audio, video').forEach(el => {
          el.muted = false;
          el.volume = 1;
        });
      });

      this.log(`Loaded episode: ${this.episodeInfo.title}`);
      return this.episodeInfo;
    } catch (error) {
      this.log(`Error loading episode: ${error.message}`, 'error');
      return null;
    }
  }

  /**
   * Start monitoring for navigations to detect episode end
   */
  startNavigationMonitoring(originalUrl) {
    if (this.navigationMonitor) {
      clearInterval(this.navigationMonitor);
    }

    this.navigationMonitor = setInterval(async () => {
      try {
        if (!this.page || this.page.isClosed()) {
          this.log('Page is closed, stopping navigation monitor');
          clearInterval(this.navigationMonitor);
          this.navigationMonitor = null;
          this.endDetected = true;
          return;
        }

        const currentUrl = await this.page.url();
        if (currentUrl !== originalUrl && !currentUrl.includes('chrome-extension://')) {
          this.log(`Navigation detected from ${originalUrl} to ${currentUrl}`);
          this.endDetected = true;
        }

        // Also check if episode has completed via showrunner-status
        const isCompleted = await this.page.evaluate(() => {
          const status = document.querySelector('.showrunner-status');
          return status && (
            status.textContent.includes('complete') ||
            status.textContent.includes('ended') ||
            status.textContent.includes('finished')
          );
        }).catch(() => false);

        if (isCompleted) {
          this.log('Episode completion detected through status element');
          this.endDetected = true;
        }
      } catch (error) {
        // Ignore errors in the monitor
      }
    }, 2000); // Check every 2 seconds
  }

  /**
   * Generate proper filename for recording
   * @param {string} extension The file extension to use (webm or mp4)
   */
  getRecordingFilename(extension = 'webm') {
    const date = new Date().toISOString().replace(/[:.]/g, '-');
    const show = (this.episodeInfo?.showTitle || 'show').replace(/[^a-zA-Z0-9]/g, '-');
    const title = (this.episodeInfo?.title || 'episode').replace(/[^a-zA-Z0-9]/g, '-');

    return path.join(this.options.outputDir, `${show}-${title}-${date}.${extension}`);
  }

  /**
   * Log with timestamp and optional verbosity control
   */
  log(message, level = 'info') {
    if (!this.options.verbose && level === 'debug') return;

    const timestamp = new Date().toISOString().split('T')[1].split('.')[0];

    switch (level) {
      case 'error':
        console.error(`[${timestamp}] ERROR: ${message}`);
        break;
      case 'warn':
        console.warn(`[${timestamp}] WARN: ${message}`);
        break;
      case 'debug':
        console.log(`[${timestamp}] DEBUG: ${message}`);
        break;
      default:
        console.log(`[${timestamp}] ${message}`);
    }
  }

  /**
   * Initialize the player
   */
  async preInitialize() {
    // Create output directory if it doesn't exist
    if (this.options.record) {
      fs.mkdirSync(this.options.outputDir, { recursive: true });
    }
    return this;
  }

  /**
   * Get the Chrome executable path based on platform
   */
  getChromePath() {
    const platform = os.platform();

    if (platform === 'win32') {
      // Windows
      return 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
    } else if (platform === 'darwin') {
      // macOS
      return '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
    } else if (platform === 'linux') {
      // Linux - try multiple possible locations
      const possiblePaths = [
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable',
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser'
      ];

      for (const chromePath of possiblePaths) {
        if (fs.existsSync(chromePath)) {
          return chromePath;
        }
      }

      // If none found, return a default and let the user know
      this.log('Could not find Chrome. Please specify the path manually.', 'warn');
      return '/usr/bin/google-chrome-stable'; // Common default location
    }

    // Fallback
    return '';
  }

  /**
   * Initialize the browser and page
   */

  async initialize() {
    this.log('Initializing browser...');
  
    // Initialize basic configuration
    await this.preInitialize();
  
    // Force WebM format when using headless mode (MP4 often not supported in headless)
    if (this.options.headless && this.options.outputFormat === 'mp4') {
      this.log('MP4 format is often not supported in headless mode, using WebM instead.', 'warn');
      this.options.outputFormat = 'webm';
    }
  
    // Calculate browser window dimensions with extra padding
    // Add extra padding to account for browser chrome/UI elements
    const windowWidth = this.options.videoWidth;
    const windowHeight = this.options.videoHeight;
  
    // Launch browser with appropriate args for audio/video and WebGL performance
    const browserArgs = [
      '--no-sandbox',
      `--ozone-override-screen-size=${windowWidth},${windowHeight}`,      
      '--disable-setuid-sandbox',
      '--no-first-run',
      '--disable-infobars',
      '--hide-crash-restore-bubble',
      '--disable-blink-features=AutomationControlled',
      '--hide-scrollbars',
      '--autoplay-policy=no-user-gesture-required',
      
      // WebGL performance improvements (from both scripts)
      '--enable-gpu-rasterization',
      '--ignore-gpu-blocklist',
      '--use-gl=angle',
      
      // Media hardware acceleration
      '--enable-accelerated-video-decode',
      '--enable-accelerated-video',
      
      // Audio improvements
      '--disable-features=AudioServiceOutOfProcess',
    ];
    
    // Add headless specific args if needed
    if (this.options.headless) {
      browserArgs.push(
        '--headless=new',
        '--enable-unsafe-swiftshader',
        '--disable-gpu-sandbox'
      );
    }
    // Get Chrome executable path
    const executablePath = this.options.executablePath || this.getChromePath();
  
    if (!executablePath) {
      throw new Error('Could not find Chrome executable. Please specify using --chrome-path=');
    }
  
    this.log(`Using Chrome at: ${executablePath}`);

    // Important: Use defaultViewport: null like in the alternative script
    this.browser = await launch({
      headless: this.options.headless ? "new" : false,
      args: browserArgs,
      executablePath: executablePath,
      defaultViewport: null // Let browser manage viewport size natively
    });  

    this.page = await this.browser.newPage();
  
    // Important: Create a CDP session for precise window control (from alternative script)
    const session = await this.page.target().createCDPSession();
    const {windowId} = await session.send('Browser.getWindowForTarget');
    
    // First get the UI size difference between outer and inner window (browser chrome)
    const uiSize = await this.page.evaluate(() => {
      return {
        height: window.outerHeight - window.innerHeight,
        width: window.outerWidth - window.innerWidth,
      };
    });
    
    // Set exact window bounds including UI chrome size
    await session.send('Browser.setWindowBounds', {
      windowId,
      bounds: {
        height: windowHeight + uiSize.height,
        width: windowWidth + uiSize.width,
      },
    });
    
    // Now set the viewport size to match our exact dimensions
    await this.page.setViewport({
      width: windowWidth,
      height: windowHeight,
      deviceScaleFactor: 1
    });
    
    // Force the document to expand to the full viewport size with CSS
    await this.page.addStyleTag({
      content: `
        html, body {
          margin: 0 !important;
          padding: 0 !important;
          width: ${windowWidth}px !important;
          height: ${windowHeight}px !important;
          overflow: hidden !important;
          background: black !important;
        }
        
        /* Target common element containers like the alternative script */
        #root, main, .app-container, .scene-container, .player-container, 
        [class*="container"], [class*="wrapper"], [class*="player"], [class*="scene"] {
          position: fixed !important;
          top: 0 !important;
          left: 0 !important;
          width: 100% !important;
          height: 100% !important;
          z-index: 1 !important;
        }
        
        /* Handle video elements specifically like the alternative script */
        video {
          position: fixed !important;
          top: 0 !important;
          left: 0 !important;
          width: 100% !important;
          height: 100% !important;
          z-index: 999000 !important;
          background: black !important;
          object-fit: contain !important;
          transform: translate(0, 0) !important;
        }
        
        /* Hide headers that might create spacing */
        .header-container, header {
          z-index: 0 !important;
        }
      `
    });
    
    // Verify the screen dimensions are correct
    const screenDimensions = await this.page.evaluate(() => ({
      screenWidth: window.screen.width,
      screenHeight: window.screen.height,
      outerWidth: window.outerWidth,
      outerHeight: window.outerHeight,
      innerWidth: window.innerWidth,
      innerHeight: window.innerHeight
    }));
    
    this.log(`Screen dimensions: ${screenDimensions.screenWidth}x${screenDimensions.screenHeight}`);
    this.log(`Outer window: ${screenDimensions.outerWidth}x${screenDimensions.outerHeight}`);
    this.log(`Viewport dimensions: ${screenDimensions.innerWidth}x${screenDimensions.innerHeight}`);
    
    // Improve navigation timeout
    this.page.setDefaultNavigationTimeout(120000);
    
    // Set up error handling
    this.setupErrorHandling();
    
    this.log('Browser initialized successfully');
    return this;
  }  

  /**
   * Set up error handling for the page
   */
  setupErrorHandling() {
    // Monitor important console messages
    this.page.on('console', msg => {
      const text = msg.text();
  
      // Add this specific check for the navigation message
      if (text.includes('Navigating to next episode:')) {
        this.log('*** Episode end detected: "Navigating to next episode" message found ***');
        this.endDetected = true;
        
        // Optionally, if you want to stop checking for other end conditions:
        if (this.navigationMonitor) {
          clearInterval(this.navigationMonitor);
          this.navigationMonitor = null;
        }
      }
  
      // Rest of your existing console message handling...
      if (msg.type() === 'error') {
        this.log(`Browser: ${text}`, 'error');
      } else if (msg.type() === 'warning') {
        this.log(`Browser: ${text}`, 'warn');
      } else if (this.options.verbose) {
        // Log all messages in verbose mode
        this.log(`Browser: ${text}`, 'debug');
      } else if (
        // Always log important messages
        text.includes('scene:') ||
        text.includes('showrunner:') ||
        text.includes('Stage3D:') ||
        text.includes('dialogue:') ||
        text.includes('playback')
      ) {
        this.log(`Browser: ${text}`);
      }
  
      // Your existing detection code can remain as a fallback
      if (text.includes('Navigating to next episode:')) {
        this.log('Detected episode completion through navigation message');
        this.endDetected = true;
      }
    });

    // Log all failed requests that might impact audio/video
    this.page.on('requestfailed', request => {
      const url = request.url();
      if (url.includes('.mp3') || url.includes('.mp4') || url.includes('media') || url.includes('audio')) {
        this.log(`Failed to load media: ${url} - ${request.failure().errorText}`, 'error');
      }
    });

    // Monitor page errors
    this.page.on('error', err => {
      this.log(`Page error: ${err.message}`, 'error');
    });

    // Listen for page close
    this.page.on('close', () => {
      this.log('Page was closed');
      this.endDetected = true;
    });
  }

   /**
   * Start playing the episode and recording
   */
  async startEpisode() {
    this.log('Starting episode playback...');
  
    try {
      // Wait for the slate to appear
      this.log('Waiting for start button...');
      await this.page.waitForFunction(() => {
        const slate = document.querySelector('.slate-ready, .slate-loading');
        return slate && window.getComputedStyle(slate).display !== 'none';
      }, { timeout: this.options.waitTimeout });
  
      // Start recording if enabled
      let videoFile = null;
  
      if (this.options.record) {
        // Double-check viewport dimensions before recording
        const viewportSize = await this.page.evaluate(() => ({
          width: window.innerWidth,
          height: window.innerHeight,
          bodyWidth: document.body.clientWidth,
          bodyHeight: document.body.clientHeight
        }));
        
        this.log(`Pre-recording dimensions check:
          Viewport: ${viewportSize.width}x${viewportSize.height}
          Body: ${viewportSize.bodyWidth}x${viewportSize.bodyHeight}`);
        
        // If dimensions don't match expected, try to fix
        if (viewportSize.height !== this.options.videoHeight || 
            viewportSize.width !== this.options.videoWidth) {
          this.log('Viewport dimensions mismatch - attempting to fix...', 'warn');
          
          // Re-apply viewport settings
          await this.page.setViewport({
            width: this.options.videoWidth,
            height: this.options.videoHeight,
            deviceScaleFactor: 1
          });
          
          // Re-apply CSS to ensure correct dimensions
          await this.page.addStyleTag({
            content: `
              html, body {
                margin: 0 !important;
                padding: 0 !important;
                width: ${this.options.videoWidth}px !important;
                height: ${this.options.videoHeight}px !important;
                overflow: hidden !important;
              }
              
              /* Ensure proper positioning for all containers */
              #root, .app-container, main, .scene-container, .player-container {
                position: absolute !important;
                top: 0 !important;
                left: 0 !important;
                width: 100% !important;
                height: 100% !important;
                overflow: hidden !important;
              }
            `
          });
        }
          
        // Generate filename
        const filename = this.getRecordingFilename(this.options.outputFormat);
        this.log(`Starting recording: ${filename}`);
  
        // Create a writable stream for the recording
        this.outputFile = fs.createWriteStream(filename);
  
        // Determine the mime type based on the requested output format
        const mimeType = this.options.outputFormat === 'mp4' ?
          "video/mp4;codecs=avc1,mp4a.40.2" : // H.264 video and AAC audio for MP4
          "video/webm;codecs=vp8,opus";       // VP8 video and Opus audio for WebM
  
        this.log(`Using codec: ${mimeType}`, 'debug');
  
        try {
          // Use the Chrome tabCapture compatible format for video constraints
          this.stream = await getStream(this.page, {
            audio: true,
            video: true,
            frameSize: 20, // Controls buffer size, not frame rate
            bitsPerSecond: 8000000, // Higher bitrate for better quality (8 Mbps)
            mimeType: mimeType,
            videoConstraints: {
              mandatory: {
                minWidth: this.options.videoWidth,
                maxWidth: this.options.videoWidth,
                minHeight: this.options.videoHeight,
                maxHeight: this.options.videoHeight,
                minFrameRate: this.options.frameRate,
                maxFrameRate: this.options.frameRate
              }
            }
          });
          
          videoFile = filename;
        } catch (error) {
          // If MP4 fails, try WebM as fallback
          if (this.options.outputFormat === 'mp4' && error.message.includes('not supported')) {
            this.log('MP4 recording failed, falling back to WebM format.', 'warn');
            this.options.outputFormat = 'webm';
        
            // Create a new output file with WebM extension
            if (this.outputFile) {
              this.outputFile.close();
            }
        
            const webmFilename = this.getRecordingFilename('webm');
            this.log(`Switching to WebM recording: ${webmFilename}`);
            this.outputFile = fs.createWriteStream(webmFilename);
        
            // Try again with WebM - using Chrome tabCapture compatible format
            this.stream = await getStream(this.page, {
              audio: true,
              video: true,
              frameSize: 20,
              bitsPerSecond: 6000000, // Slightly lower bitrate for WebM
              mimeType: "video/webm;codecs=vp8,opus",
              videoConstraints: {
                mandatory: {
                  minWidth: this.options.videoWidth,
                  maxWidth: this.options.videoWidth,
                  minHeight: this.options.videoHeight,
                  maxHeight: this.options.videoHeight,
                  maxFrameRate: this.options.frameRate
                }
              }
            });
        
            videoFile = webmFilename;
          } else {
            // Log detailed error info
            this.log(`Recording error: ${error.message}`, 'error');
            throw error;
          }
        }  
   
        // Pipe the stream to the file
        this.stream.pipe(this.outputFile);
        
        // Log successful recording start
        this.log(`Recording started with dimensions ${this.options.videoWidth}x${this.options.videoHeight}`);
      }

      // Click the "Touch to Begin" button
      this.log('Clicking start button...');
      try {
        // Try multiple methods to ensure click works
        const clickResult = await this.page.evaluate(() => {
          // Find any potential start buttons using common selectors
          const startBtns = [
            document.querySelector('.slate-ready'),
            document.querySelector('.start-button'),
            document.querySelector('[data-action="start"]'),
            document.querySelector('button:contains("Begin")'),
            document.querySelector('button:contains("Start")'),
            ...Array.from(document.querySelectorAll('button')).filter(el => 
              el.textContent.toLowerCase().includes('start') || 
              el.textContent.toLowerCase().includes('begin')
            )
          ].filter(Boolean);
          
          if (startBtns.length > 0) {
            // Try clicking each button until one works
            for (const btn of startBtns) {
              try {
                btn.click();
                return `Clicked button: ${btn.outerHTML.substring(0, 50)}...`;
              } catch (e) {
                // Continue to next button
              }
            }
            return 'Found buttons but clicks failed';
          } else {
            // Try clicking on common slate areas if no buttons found
            const slateElements = [
              document.querySelector('.slate'),
              document.querySelector('.slate-container'),
              document.querySelector('.player-container')
            ].filter(Boolean);
            
            for (const el of slateElements) {
              try {
                el.click();
                return `Clicked slate element: ${el.outerHTML.substring(0, 50)}...`;
              } catch (e) {
                // Continue to next element
              }
            }
            
            return 'No suitable click targets found';
          }
        });
        
        this.log(`Click result: ${clickResult}`);
      } catch (error) {
        this.log(`Direct click failed: ${error.message}`, 'warn');
        
        // Try puppeteer's built-in click as a fallback
        try {
          await this.page.click('.slate-ready, .start-button, [data-action="start"]');
          this.log('Fallback click succeeded');
        } catch (clickError) {
          this.log('All click attempts failed - episode may not start properly', 'error');
        }
      }
 
      // Wait for scene to load
      this.log('Waiting for scene to load...');
      try {
        await this.page.waitForFunction(() => {
          return (
            document.querySelector('.slate-ready, .slate-loading')?.style.display === 'none' ||
            document.querySelector('.now-playing-container[data-field="dialogue_line"] .now-playing-text')?.textContent !== '' ||
            document.querySelector('.dialogue-text')?.textContent !== ''
          );
        }, { timeout: this.options.waitTimeout });
        this.log('Scene loaded successfully');
      } catch (error) {
        this.log('Could not detect scene load, continuing anyway...', 'warn');
      }
 
      // Set up audio
      await this.ensureAudioEnabled();
 
      this.log('Episode playback started');
      return { videoFile };
    } catch (error) {
      this.log(`Error starting episode: ${error.message}`, 'error');
      return { videoFile: null };
    }
  }

  /**
   * Make sure audio is enabled for the page
   */
  async ensureAudioEnabled() {
    // Ensure audio isn't muted
    await this.page.evaluate(() => {
      // Find and unmute all audio elements
      function enableAudio() {
        document.querySelectorAll('audio, video').forEach(el => {
          if (el.paused) {
            el.play().catch(() => {});
          }
          el.muted = false;
          el.volume = 1;
        });

        // Look for the speaker-audio element and unmute it
        const speakerAudio = document.getElementById('speaker-audio');
        if (speakerAudio) {
          if (speakerAudio.paused) {
            speakerAudio.play().catch(() => {});
          }
          speakerAudio.muted = false;
          speakerAudio.volume = 1;
        }

        // Also check for iframe content if available
        try {
          document.querySelectorAll('iframe').forEach(iframe => {
            try {
              const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
              iframeDoc.querySelectorAll('audio, video').forEach(el => {
                if (el.paused) {
                  el.play().catch(() => {});
                }
                el.muted = false;
                el.volume = 1;
              });
            } catch (e) {
              // Cross-origin access might be blocked
            }
          });
        } catch (e) {}
      }

      // Run immediately and again after a delay
      enableAudio();
      setTimeout(enableAudio, 1000);
      setTimeout(enableAudio, 3000);
    });
  }

  /**
   * Wait for the episode to finish
   * @param {number} timeout Maximum time to wait in milliseconds
   */
  async waitForEpisodeToFinish(timeout = 3600000) {
    this.log(`Waiting for episode to finish (timeout: ${timeout}ms)...`);
  
    const startTime = Date.now();
    let statusInterval;
  
    try {
      // Reset end detection flag
      this.endDetected = false;
      
      // Add a one-time console message listener specifically for episode end
      const navigationDetected = new Promise(resolve => {
        const onConsoleMessage = (msg) => {
          const text = msg.text();
          if (text.includes('Navigating to next episode:')) {
            this.log('Episode end detected: "Navigating to next episode" message found');
            this.endDetected = true;
            // Use .off() instead of .removeListener() - this is the Puppeteer way
            this.page.off('console', onConsoleMessage);
            resolve(true);
          }
        };
        
        this.page.on('console', onConsoleMessage);
      });
      
      // Set up a status log interval (keep this for visibility)
      statusInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        this.log(`Still waiting... (${Math.floor(elapsed / 60)}m ${elapsed % 60}s elapsed)`);
      }, 30000); // Log status every 30 seconds
  
      // Wait for either the navigation event or timeout
      const timeoutPromise = new Promise(resolve => {
        setTimeout(() => {
          this.log('Episode wait timeout reached', 'warn');
          resolve(false);
        }, timeout);
      });
  
      // Wait for either the navigation event or timeout
      await Promise.race([navigationDetected, timeoutPromise]);
  
      // Clean up interval
      if (statusInterval) {
        clearInterval(statusInterval);
        statusInterval = null;
      }
  
      // Short delay to ensure complete capture
      //await new Promise(r => setTimeout(r, 1000));
  
      return this.endDetected;
    } catch (error) {
      this.log(`Error waiting for episode to finish: ${error.message}`, 'error');
      if (statusInterval) {
        clearInterval(statusInterval);
      }
      return false;
    } finally {
      // Stop navigation monitoring
      if (this.navigationMonitor) {
        clearInterval(this.navigationMonitor);
        this.navigationMonitor = null;
      }
    }
  }

  /**
   * Stop recording and clean up resources
   */
  async close() {
    this.log('Cleaning up resources...');

    // Stop navigation monitoring if active
    if (this.navigationMonitor) {
      clearInterval(this.navigationMonitor);
      this.navigationMonitor = null;
    }

    // Stop recording if active
    if (this.stream) {
      try {
        this.log('Stopping recording...');
        // Wait briefly to ensure all data is written
        await new Promise(r => setTimeout(r, 1000));
        await this.stream.destroy();
        this.log('Recording stopped');
        this.log(`Video saved to: ${this.outputFile?.path || "unknown path"}`);
      } catch (error) {
        this.log(`Error stopping recording: ${error.message}`, 'error');
      }
    }

    // Close the browser
    if (this.browser) {
      try {
        await this.browser.close();
        this.log('Browser closed');
      } catch (error) {
        this.log(`Error closing browser: ${error.message}`, 'error');
      }
    }

    // Close WebSocket server
    try {
      if (wss) (await wss).close();
      this.log('WebSocket server closed');
    } catch (error) {
      this.log(`Error closing WebSocket server: ${error.message}`, 'error');
    }

    this.log('All resources cleaned up');
  }
}

/**
 * Run the player with command line arguments
 */
async function main() {
  const args = process.argv.slice(2);

  // Extract options
  const headless = args.includes('--headless');
  const noRecord = args.includes('--no-record');
  const verbose = !args.includes('--quiet');
  const url = args.find(arg => !arg.startsWith('--')) || 'https://shmotime.com/shmotime_episode/the-security-sentinel/';
  const waitTime = parseInt(args.find(arg => arg.startsWith('--wait='))?.split('=')[1] || '3600000', 10);
  const outputDir = args.find(arg => arg.startsWith('--output='))?.split('=')[1] || './recordings';
  const chromePath = args.find(arg => arg.startsWith('--chrome-path='))?.split('=')[1] || '';
  const outputFormat = args.find(arg => arg.startsWith('--format='))?.split('=')[1] || 'mp4';
  const viewportHeight = parseInt(args.find(arg => arg.startsWith('--height='))?.split('=')[1] || '1080', 10);
  const viewportWidth = parseInt(args.find(arg => arg.startsWith('--width='))?.split('=')[1] || '1920', 10);
  const frameRate = parseInt(args.find(arg => arg.startsWith('--fps='))?.split('=')[1] || '30', 10);

  console.log('Shmotime Player starting...');
  console.log(`URL: ${url}`);
  console.log(`Settings: headless=${headless}, record=${!noRecord}, format=${outputFormat}, verbose=${verbose}`);
  console.log(`Video: ${viewportWidth}x${viewportHeight}@${frameRate}fps`);

  // Create and run the player
  const player = new ShmotimePlayer({
    headless,
    record: !noRecord,
    verbose,
    outputDir,
    waitTimeout: 60000,
    executablePath: chromePath,
    outputFormat,
    videoWidth: viewportWidth,
    videoHeight: viewportHeight,
    frameRate
  });

  try {
    // Initialize browser
    await player.initialize();

    // Load episode
    const episodeInfo = await player.loadEpisodeUrl(url);
    if (!episodeInfo) {
      throw new Error('Failed to load episode');
    }

    // Start episode and recording
    const { videoFile } = await player.startEpisode();
    if (!videoFile && !noRecord) {
      throw new Error('Failed to start episode recording');
    }

    // Wait for episode to finish
    await player.waitForEpisodeToFinish(waitTime);

    console.log('Episode processing complete');
    if (videoFile) console.log(`Video will be saved to: ${videoFile}`);

  } catch (error) {
    console.error(`Main process error: ${error.message}`);
  } finally {
    // Always clean up resources
    await player.close();
    console.log('Process complete');
    process.exit(0); // Ensure process exits
  }
}

// Run if called directly
if (require.main === module) {
  main().catch(error => {
    console.error(`Fatal error: ${error.message}`);
    process.exit(1);
  });
}

module.exports = ShmotimePlayer;
