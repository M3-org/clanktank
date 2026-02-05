const { launch, getStream, wss } = require('puppeteer-stream');
const path = require('path');
const fs = require('fs');
const os = require('os');

/**
 * Enhanced class to automate playback of Shmotime episodes with video and audio recording
 * using puppeteer-stream for native browser audio/video capture
 * 
 * Now includes support for new recorder events and data schema export
 */
class ShmotimePlayerV2 {
  /**
   * Create a new ShmotimePlayerV2 instance
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
      exportData: true, // Export processed show/episode data
      stopRecordingAt: 'end_credits', // Event at which to stop recording (end_credits, end_ep, end_postcredits)
      fixFrameRate: true, // Post-process with ffmpeg to fix frame rate
      // Video resolution settings
      videoWidth: 1920,
      videoHeight: 1080,
      frameRate: 30, // Target frame rate for ffmpeg post-processing
      ...options
    };

    this.browser = null;
    this.page = null;
    this.stream = null;
    this.outputFile = null;
    this.episodeInfo = null;
    this.navigationMonitor = null;
    this.endDetected = false;
    this.recordingStopped = false;

    // New data storage for schema v2
    this.showConfig = null;
    this.episodeData = null;
    this.recorderEvents = [];
    this.currentPhase = 'waiting'; // waiting, intro, episode, credits, postcredits, ended
  }

  /**
   * Get the Chrome executable path based on platform
   * @returns {string} Path to Chrome executable
   */
  getChromePath() {
    const platform = os.platform();
    const log = this.log.bind(this); // Ensure log context

    if (platform === 'win32') {
      return 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
    } else if (platform === 'darwin') {
      return '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
    } else if (platform === 'linux') {
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
      log('Could not find Chrome. Please specify the path manually.', 'warn');
      return '/usr/bin/google-chrome-stable';
    }
    return '';
  }

  /**
   * Fix video frame rate using ffmpeg post-processing
   */
  async fixVideoFrameRateWithFfmpeg() {
    const log = this.log.bind(this); // Ensure log context
    if (!this.outputFile || !this.outputFile.path) {
      log('No output file to process for ffmpeg.', 'warn');
      return null;
    }
    const inputFile = this.outputFile.path;
    const targetFrameRate = this.options.frameRate;

    try {
      const { exec } = require('child_process'); // Keep require inside for lazy loading
      const util = require('util');
      const execAsync = util.promisify(exec);
      
      const outputPath = inputFile.replace(/(\.\w+)$/, `_fps${targetFrameRate}$1`);
      
      log(`Post-processing video with ffmpeg to ${targetFrameRate}fps...`);
      log(`Input: ${inputFile}, Output: ${outputPath}`);
      
      const ffmpegCmd = `ffmpeg -i "${inputFile}" -c copy -r ${targetFrameRate} -y "${outputPath}"`;
      
      const { stdout, stderr } = await execAsync(ffmpegCmd);
      if (stderr) {
          log(`FFmpeg stderr: ${stderr}`, 'debug');
      }
      
      log(`Frame rate corrected: ${outputPath}`);
      log(`Original file: ${inputFile}`);
      return outputPath;
      
    } catch (error) {
      log(`Error fixing frame rate with ffmpeg: ${error.message}`, 'error');
      log('You can manually fix the frame rate with:', 'info');
      log(`ffmpeg -i "${inputFile}" -c copy -r ${targetFrameRate} "${inputFile.replace(/(\.\w+)$/, `_fps${targetFrameRate}$1`)}"`, 'info');
      return null;
    }
  }

  /**
   * Process and store show config data
   * @param {Object} showConfig Raw show config from recorder:load_show
   */
  processShowConfig(showConfig) {
    this.log('Processing show config data...');
    
    // Store the processed show config according to new schema
    this.showConfig = {
      description: showConfig.description || '',
      id: showConfig.id || '',
      creator: showConfig.creator || '',
      image: showConfig.image || false,
      image_thumb: showConfig.image_thumb || false,
      actors: {},
      locations: {}
    };

    // Process actors
    if (showConfig.actors) {
      Object.keys(showConfig.actors).forEach(actorId => {
        const actor = showConfig.actors[actorId];
        this.showConfig.actors[actorId] = {
          description: actor.description || '',
          elevenlabs_voice_id: actor.elevenlabs_voice_id || '',
          image: actor.image || '',
          image_thumb: actor.image_thumb || '',
          title: actor.title || ''
        };
      });
    }

    // Process locations
    if (showConfig.locations) {
      Object.keys(showConfig.locations).forEach(locationId => {
        const location = showConfig.locations[locationId];
        this.showConfig.locations[locationId] = {
          description: location.description || '',
          image: location.image || '',
          image_thumb: location.image_thumb || '',
          title: location.title || '',
          slots: {
            north_pod: location.slots?.north_pod || '',
            south_pod: location.slots?.south_pod || '',
            east_pod: location.slots?.east_pod || '',
            west_pod: location.slots?.west_pod || '',
            center_pod: location.slots?.center_pod || ''
          }
        };
      });
    }

    this.log(`Processed show config: ${Object.keys(this.showConfig.actors).length} actors, ${Object.keys(this.showConfig.locations).length} locations`);
  }

  /**
   * Process and store episode data
   * @param {Object} episodeData Raw episode data from recorder:load_episode
   */
  processEpisodeData(episodeData) {
    this.log('Processing episode data...');
    
    // Store the processed episode data according to new schema
    this.episodeData = {
      id: episodeData.id || '',
      image: episodeData.image || false,
      image_thumb: episodeData.image_thumb || false,
      premise: episodeData.premise || '',
      scenes: []
    };

    // Process scenes
    if (episodeData.scenes && Array.isArray(episodeData.scenes)) {
      this.episodeData.scenes = episodeData.scenes.map(scene => ({
        description: scene.description || '',
        totalInScenes: scene.totalInScenes || 0,
        transitionIn: scene.transitionIn || '',
        transitionOut: scene.transitionOut || '',
        
        // Cast references - convert to actor ID strings
        cast: {
          center_pod: scene.cast?.center_pod || undefined,
          east_pod: scene.cast?.east_pod || undefined,
          north_pod: scene.cast?.north_pod || undefined,
          south_pod: scene.cast?.south_pod || undefined,
          west_pod: scene.cast?.west_pod || undefined
        },
        
        // Location reference - just the location ID string
        location: scene.location || '',
        
        // Dialogues array
        dialogues: (scene.dialogues || []).map(dialogue => ({
          number: dialogue.number || 0,
          totalInScenes: dialogue.totalInScenes || 0,
          action: dialogue.action || '',
          line: dialogue.line || '',
          actor: dialogue.actor || '' // Actor ID string reference
        })),
        
        // Scene statistics
        length: scene.length || 0,
        number: scene.number || 0,
        totalInEpisode: scene.totalInEpisode || 0,
        total_dialogues: scene.total_dialogues || 0
      }));
    }

    this.log(`Processed episode data: ${this.episodeData.scenes.length} scenes`);
  }

  /**
   * Stop recording if it's currently active
   */
  async stopRecording() {
    if (this.stream && !this.recordingStopped) {
      try {
        this.log('Stopping recording immediately...');
        this.recordingStopped = true;
        
        // Stop immediately without delay for precision
        await this.stream.destroy();
        
        this.log('Recording stopped');
        this.log(`Video saved to: ${this.outputFile?.path || "unknown path"}`);
        
        // Close the output file
        if (this.outputFile) {
          this.outputFile.end();
        }

        // Post-process with ffmpeg to fix frame rate
        if (this.options.fixFrameRate && this.outputFile?.path) {
          // Intentionally not awaiting this promise - let it run in background
          this.fixVideoFrameRateWithFfmpeg()
            .then(processedPath => {
              if (processedPath) {
                this.log(`FFmpeg post-processing completed for: ${processedPath}`);
                // Optionally, update this.outputFile.path or handle the new file path
              }
            })
            .catch(err => {
              this.log(`FFmpeg post-processing failed in background: ${err.message}`, 'warn');
            });
        }

        // Close browser to stop audio playback after a brief delay to ensure recording is finalized
        setTimeout(async () => {
          if (this.browser && !this.browser.process()?.killed) {
            try {
              this.log('Closing browser to stop audio playback...');
              await this.browser.close();
              this.log('Browser closed after recording stop');
            } catch (error) {
              this.log(`Error closing browser after recording: ${error.message}`, 'warn');
            }
          }
        }, 500);
        
      } catch (error) {
        this.log(`Error stopping recording: ${error.message}`, 'error');
      }
    }
  }

  /**
   * Handle recorder events from console messages
   * @param {string} eventType The event type (e.g., 'start_intro', 'load_show')
   * @param {Object|null} eventData Optional data payload for events like load_show/load_episode
   */
  handleRecorderEvent(eventType, eventData = null) {
    const timestamp = new Date().toISOString();
    
    this.log(`Recorder event: ${eventType}`);
    
    // Store the event
    this.recorderEvents.push({
      type: eventType,
      timestamp,
      data: eventData
    });

    switch (eventType) {
      case 'load_show':
        if (eventData) {
          this.processShowConfig(eventData);
        }
        break;
        
      case 'load_episode':
        if (eventData) {
          this.processEpisodeData(eventData);
        }
        break;
        
      case 'start_intro':
        this.currentPhase = 'intro';
        break;
        
      case 'end_intro':
        this.currentPhase = 'waiting';
        break;
        
      case 'start_ep':
        this.currentPhase = 'episode';
        break;
        
      case 'end_ep':
        this.currentPhase = 'waiting';
        // Check if we should stop recording here with minimal delay for precision
        if (this.options.stopRecordingAt === 'end_ep') {
          setTimeout(() => this.stopRecording(), 100);
        }
        break;
        
      case 'start_credits':
        this.currentPhase = 'credits';
        break;
        
      case 'end_credits':
        this.currentPhase = 'waiting';
        // Check if we should stop recording here (default behavior) with minimal delay for precision
        if (this.options.stopRecordingAt === 'end_credits') {
          setTimeout(() => this.stopRecording(), 100);
        }
        break;
        
      case 'start_postcredits':
        this.currentPhase = 'postcredits';
        break;
        
      case 'end_postcredits':
        this.currentPhase = 'ended';
        this.endDetected = true;
        this.log('*** Episode end detected: end_postcredits event ***');
        
        // Check if we should stop recording here with minimal delay for precision
        if (this.options.stopRecordingAt === 'end_postcredits') {
          setTimeout(() => this.stopRecording(), 100);
        }
        
        // Stop navigation monitoring since we have definitive end
        if (this.navigationMonitor) {
          clearInterval(this.navigationMonitor);
          this.navigationMonitor = null;
        }
        break;
    }
  }

  /**
   * Export processed data to JSON files
   */
  async exportProcessedData() {
    if (!this.options.exportData) return;

    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const baseFilename = this.episodeInfo?.episodeId || this.episodeData?.id || 'episode';
      
      // Export show config (still useful as a separate file for some use cases)
      if (this.showConfig) {
        const showConfigPath = path.join(this.options.outputDir, `${baseFilename}-show-config-${timestamp}.json`);
        fs.writeFileSync(showConfigPath, JSON.stringify(this.showConfig, null, 2));
        this.log(`Show config exported to: ${showConfigPath}`);
      }

      // Export episode data (still useful as a separate file)
      if (this.episodeData) {
        const episodeDataPath = path.join(this.options.outputDir, `${baseFilename}-episode-data-${timestamp}.json`);
        fs.writeFileSync(episodeDataPath, JSON.stringify(this.episodeData, null, 2));
        this.log(`Episode data exported to: ${episodeDataPath}`);
      }

      // Export recorder events log with embedded show and episode data
      const eventsPath = path.join(this.options.outputDir, `${baseFilename}-events-${timestamp}.json`);
      fs.writeFileSync(eventsPath, JSON.stringify({
        episode_id: this.episodeData?.id || '',
        show_id: this.showConfig?.id || '',
        recording_session: {
          start_time: this.recorderEvents[0]?.timestamp,
          end_time: this.recorderEvents[this.recorderEvents.length - 1]?.timestamp,
          total_events: this.recorderEvents.length,
          options: this.options // Include recorder options used for this session
        },
        show_config: this.showConfig, // Embed full show config
        episode_data: this.episodeData, // Embed full episode data
        events: this.recorderEvents
      }, null, 2));
      this.log(`Recorder events log (with full data) exported to: ${eventsPath}`);

    } catch (error) {
      this.log(`Error exporting data: ${error.message}`, 'error');
    }
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
      await this.page.setCacheEnabled(false);

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
    if (this.options.record || this.options.exportData) {
      fs.mkdirSync(this.options.outputDir, { recursive: true });
    }
    return this;
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
      
      // Frame rate and video recording improvements
      '--force-video-overlays',
      '--enable-features=VaapiVideoDecoder',
      '--disable-features=VizDisplayCompositor',
      `--force-device-scale-factor=1`,
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
    this.page.on('console', async msg => { // Make the handler async
      const msgArgs = msg.args();
      if (msgArgs.length === 0) {
        // If no arguments, try to log the raw message text for debugging if verbose
        if (this.options.verbose) this.log(`Browser (empty console args): ${msg.text()}`, 'debug');
        return;
      }

      let eventText = '';
      try {
        // Attempt to get the first argument as a string, assuming it's the event type or main message
        eventText = await msgArgs[0].jsonValue(); 
      } catch (e) {
        // Fallback for complex objects or if jsonValue fails for the first arg
        eventText = msg.text(); 
      }
      
      // Ensure eventText is a string before proceeding
      if (typeof eventText !== 'string') {
        if (this.options.verbose) this.log(`Browser (non-string eventText after processing arg[0]): ${msg.text()}`, 'debug');
        eventText = msg.text(); // Final fallback to raw message text if conversion failed
        if (typeof eventText !== 'string') { // If still not a string, we cannot parse it as an event
             if (this.options.verbose) this.log(`Browser (eventText still not a string, cannot parse event): ${msg.text()}`, 'debug');
             return;
        }
      }

      if (eventText.startsWith('recorder:')) {
        try {
          const eventTypeMatch = eventText.match(/^recorder:(\w+)/);
          if (eventTypeMatch) {
            const eventType = eventTypeMatch[1];
            let eventData = null;

            // Check if there's a second argument for data
            if (msgArgs.length > 1) {
              try {
                eventData = await msgArgs[1].jsonValue();
              } catch (jsonError) {
                this.log(`Failed to get JSON value for recorder event data (${eventType}): ${jsonError.message}`, 'warn');
                try {
                    // Attempt to get a string representation of the second argument if jsonValue fails
                    const rawDataText = await msgArgs[1].evaluate(arg => {
                        if (arg instanceof Error) return arg.message;
                        if (arg instanceof Object) return JSON.stringify(arg);
                        return String(arg);
                    });
                    this.log(`Raw event data for ${eventType} (fallback): ${rawDataText}`, 'debug');
                    // Optionally, try to parse if it looks like a stringified JSON by chance
                    if (typeof rawDataText === 'string' && (rawDataText.startsWith('{') || rawDataText.startsWith('['))) {
                        try { eventData = JSON.parse(rawDataText); } catch (e) { /* ignore parse error */ }
                    }
                } catch (rawDataError) {
                    this.log(`Could not get raw string/JSON for event data ${eventType}: ${rawDataError.message}`, 'debug');
                }
              }
            }
            this.handleRecorderEvent(eventType, eventData);
            return; // Processed as a recorder event, stop further processing
          }
        } catch (error) {
          this.log(`Error processing recorder event (${eventText}): ${error.message}`, 'error');
        }
      }

      // Fallback to legacy navigation detection and regular console message handling
      if (eventText.includes('Navigating to next episode:')) {
        this.log('*** Episode end detected: "Navigating to next episode" message found ***');
        this.endDetected = true;
        if (this.navigationMonitor) {
          clearInterval(this.navigationMonitor);
          this.navigationMonitor = null;
        }
      }

      if (msg.type() === 'error') {
        this.log(`Browser: ${eventText}`, 'error');
      } else if (msg.type() === 'warning') {
        this.log(`Browser: ${eventText}`, 'warn');
      } else if (this.options.verbose) {
        this.log(`Browser: ${eventText}`, 'debug');
      } else if (
        eventText.includes('scene:') ||
        eventText.includes('showrunner:') ||
        eventText.includes('Stage3D:') ||
        eventText.includes('dialogue:') ||
        eventText.includes('playback')
      ) {
        this.log(`Browser: ${eventText}`);
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
          // Chrome tabCapture API requires boolean for video, frame rate controlled by frameSize
          this.stream = await getStream(this.page, {
            audio: true,
            video: true, // Must be boolean for tabCapture API
            frameSize: 1000, // Data chunk interval in ms (1 second chunks)
            bitsPerSecond: 8000000, // Higher bitrate for better quality (8 Mbps)
            mimeType: mimeType
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
        
            // Try again with WebM - Chrome tabCapture API format
            this.stream = await getStream(this.page, {
              audio: true,
              video: true, // Must be boolean for tabCapture API
              frameSize: 1000, // Data chunk interval in ms (1 second chunks)
              bitsPerSecond: 6000000, // Slightly lower bitrate for WebM
              mimeType: "video/webm;codecs=vp8,opus"
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
        
        // Log successful recording start with detailed info
        this.log(`Recording started with dimensions ${this.options.videoWidth}x${this.options.videoHeight} @ ${this.options.frameRate}fps`);
        this.log(`Stream settings: frameSize=1000ms, codec=${mimeType}`, 'debug');
        this.log(`FFmpeg will set final frame rate to ${this.options.frameRate}fps during post-processing.`, 'debug');
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
   * Wait for the episode to finish using new recorder events
   * @param {number} timeout Maximum time to wait in milliseconds
   */
  async waitForEpisodeToFinish(timeout = 3600000) {
    this.log(`Waiting for episode to finish using recorder events (timeout: ${timeout}ms)...`);
  
    const startTime = Date.now();
    let statusInterval;
  
    try {
      // Reset end detection flag
      this.endDetected = false;
      
      // Set up a status log interval
      statusInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        this.log(`Still waiting... (${Math.floor(elapsed / 60)}m ${elapsed % 60}s elapsed) - Current phase: ${this.currentPhase}`);
        
        // Log recent events for debugging
        const recentEvents = this.recorderEvents.slice(-3).map(e => e.type).join(', ');
        if (recentEvents) {
          this.log(`Recent events: ${recentEvents}`);
        }
      }, 1000);
  
      // Wait for the episode to finish
      await new Promise(resolve => {
        const finishTimeout = setTimeout(() => {
          clearInterval(statusInterval);
          resolve();
        }, timeout);
  
        // Wait for end detection
        const endTimeout = setTimeout(() => {
          if (this.endDetected) {
            clearInterval(statusInterval);
            resolve();
          }
        }, 1000);
      });
  
      this.log('Episode finished');
    } catch (error) {
      this.log(`Error waiting for episode to finish: ${error.message}`, 'error');
    }
  }
}

module.exports = ShmotimePlayerV2;