const { launch, getStream, wss } = require('puppeteer-stream');
const path = require('path');
const fs = require('fs');
const os = require('os');

class ShmotimeRecorder {
  constructor(options = {}) {
    // Selectors for UI elements
    this.SLATE_BUTTON_SELECTORS = [
      '.slate-ready',
      '.start-button',
      '[data-action="start"]',
    ];
    this.TEXT_BUTTON_SELECTORS_LOWERCASE = ['start', 'begin'];
    this.SLATE_CONTAINER_SELECTORS = [
        '.slate',
        '.slate-container',
        '.player-container'
    ];
    this.SLATE_WAIT_SELECTOR = '.slate-ready, .slate-loading';
    this.DIALOGUE_TEXT_SELECTORS = [
        '.now-playing-container[data-field="dialogue_line"] .now-playing-text',
        '.dialogue-text'
    ];

    this.options = {
      headless: false,
      record: true,
      verbose: true,
      outputDir: './recordings',
      waitTimeout: 60000,
      outputFormat: 'mp4',
      exportData: true,
      stopRecordingAt: 'end_credits',
      fixFrameRate: true,
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
    this.recordingStopped = false;
    this.showConfig = null;
    this.episodeData = null;
    this.recorderEvents = [];
    this.currentPhase = 'waiting';
  }

  getChromePath() {
    const platform = os.platform();
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
        if (fs.existsSync(chromePath)) return chromePath;
      }
      return '/usr/bin/google-chrome-stable';
    }
    return '';
  }

  async fixVideoFrameRateWithFfmpeg() {
    const log = this.log.bind(this); 
    if (!this.outputFile?.path || !this.options.fixFrameRate) {
        log('Skipping ffmpeg frame rate fix (no input file or option disabled).', 'debug');
        return null;
    }
    
    const inputFile = this.outputFile.path;
    const targetFrameRate = this.options.frameRate;
    const outputPath = inputFile.replace(/(\.\w+)$/, `_fps${targetFrameRate}.mp4`); // Output as MP4

    try {
      const { exec } = require('child_process');
      const util = require('util');
      const execAsync = util.promisify(exec);
      
      log(`Post-processing video to ${targetFrameRate}fps MP4: ${outputPath}`);
      log(`Input: ${inputFile}`);
      
      // Re-encode to H.264 video and AAC audio for MP4 compatibility
      const ffmpegCmd = `ffmpeg -i "${inputFile}" -r ${targetFrameRate} -c:v libx264 -preset medium -crf 23 -c:a aac -strict experimental -b:a 192k -y "${outputPath}"`;
      
      const { stdout, stderr } = await execAsync(ffmpegCmd);
      if (stderr && this.options.verbose) {
          log(`FFmpeg stderr: ${stderr}`, 'debug');
      }
      
      log(`Video processed to MP4: ${outputPath}`);
      return outputPath;
      
    } catch (error) {
      log(`Error processing video with ffmpeg: ${error.message}`, 'error');
      log('You can manually process with a command like:', 'info');
      log(`ffmpeg -i "${inputFile}" -r ${targetFrameRate} -c:v libx264 -c:a aac -strict experimental "${outputPath}"`, 'info');
      return null;
    }
  }

  processShowConfig(showConfig) {
    this.log('Processing show config data...');
    this.showConfig = {
      description: showConfig.description || '',
      id: showConfig.id || '',
      creator: showConfig.creator || '',
      image: showConfig.image || false,
      image_thumb: showConfig.image_thumb || false,
      actors: {},
      locations: {}
    };

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

  processEpisodeData(episodeData) {
    this.log('Processing episode data...');
    this.episodeData = {
      id: episodeData.id || '',
      image: episodeData.image || false,
      image_thumb: episodeData.image_thumb || false,
      premise: episodeData.premise || '',
      scenes: []
    };

    if (episodeData.scenes && Array.isArray(episodeData.scenes)) {
      this.episodeData.scenes = episodeData.scenes.map(scene => ({
        description: scene.description || '',
        totalInScenes: scene.totalInScenes || 0,
        transitionIn: scene.transitionIn || '',
        transitionOut: scene.transitionOut || '',
        cast: {
          center_pod: scene.cast?.center_pod || undefined,
          east_pod: scene.cast?.east_pod || undefined,
          north_pod: scene.cast?.north_pod || undefined,
          south_pod: scene.cast?.south_pod || undefined,
          west_pod: scene.cast?.west_pod || undefined
        },
        location: scene.location || '',
        dialogues: (scene.dialogues || []).map(dialogue => ({
          number: dialogue.number || 0,
          totalInScenes: dialogue.totalInScenes || 0,
          action: dialogue.action || '',
          line: dialogue.line || '',
          actor: dialogue.actor || ''
        })),
        length: scene.length || 0,
        number: scene.number || 0,
        totalInEpisode: scene.totalInEpisode || 0,
        total_dialogues: scene.total_dialogues || 0
      }));
    }

    this.log(`Processed episode data: ${this.episodeData.scenes.length} scenes`);
  }

  async stopRecording() {
    if (this.stream && !this.recordingStopped) {
      try {
        this.log('Stopping recording immediately...');
        this.recordingStopped = true;
        await this.stream.destroy();
        this.log('Recording stopped');
        this.log(`Video saved to: ${this.outputFile?.path || "unknown path"}`);
        
        if (this.outputFile) this.outputFile.end();

        if (this.options.fixFrameRate && this.outputFile?.path) {
          this.fixVideoFrameRateWithFfmpeg()
            .then(processedPath => {
              if (processedPath) {
                this.log(`FFmpeg post-processing completed for: ${processedPath}`);
              }
            })
            .catch(err => {
              this.log(`FFmpeg post-processing failed in background: ${err.message}`, 'warn');
            });
        }

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

  handleRecorderEvent(eventType, eventData = null) {
    const timestamp = new Date().toISOString();
    this.log(`Recorder event: ${eventType}`);
    
    this.recorderEvents.push({
      type: eventType,
      timestamp,
      data: eventData
    });

    switch (eventType) {
      case 'load_show':
        if (eventData) this.processShowConfig(eventData);
        break;
      case 'load_episode':
        if (eventData) this.processEpisodeData(eventData);
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
        if (this.options.stopRecordingAt === 'end_ep') {
          setTimeout(() => this.stopRecording(), 100);
        }
        break;
      case 'start_credits':
        this.currentPhase = 'credits';
        break;
      case 'end_credits':
        this.currentPhase = 'waiting';
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
        if (this.options.stopRecordingAt === 'end_postcredits') {
          setTimeout(() => this.stopRecording(), 100);
        }
        if (this.navigationMonitor) {
          clearInterval(this.navigationMonitor);
          this.navigationMonitor = null;
        }
        break;
    }
  }

  async exportProcessedData() {
    if (!this.options.exportData) return;

    try {
      let baseNameForLog;
      const jsonExportTimestamp = new Date().toISOString().replace(/[:.]/g, '-');

      if (this.outputFile?.path) {
        // If a video was recorded, base the JSON name on the video filename (without its extension)
        baseNameForLog = path.basename(this.outputFile.path).replace(/\.\w+$/, '');
      } else {
        // If no video, create a unique name for the JSON log using current timestamp
        const showPart = (this.episodeInfo?.showTitle || this.showConfig?.title || 'show').replace(/[^a-zA-Z0-9]/g, '-');
        const titlePart = (this.episodeInfo?.title || this.episodeData?.title || this.episodeData?.id || 'episode').replace(/[^a-zA-Z0-9]/g, '-');
        baseNameForLog = `${showPart}-${titlePart}-${jsonExportTimestamp}`;
      }

      const finalJsonPath = path.join(this.options.outputDir, `${baseNameForLog}-session-log.json`);

      if (this.showConfig || this.episodeData || this.recorderEvents.length > 0) {
        fs.writeFileSync(finalJsonPath, JSON.stringify({
          episode_id: this.episodeData?.id || this.episodeInfo?.episodeId || null,
          show_id: this.showConfig?.id || null,
          recording_session_options: this.options,
          show_config: this.showConfig || null, 
          episode_data: this.episodeData || null, 
          event_timeline: this.recorderEvents,
          // Add references to the video files for clarity in the JSON
          original_video_file: this.outputFile?.path ? path.basename(this.outputFile.path) : null,
          processed_mp4_file: this.outputFile?.path ? path.basename(this.outputFile.path).replace(/(\.\w+)$/, `_fps${this.options.frameRate}.mp4`) : null
        }, null, 2));
        this.log(`Comprehensive session log exported to: ${finalJsonPath}`);
      } else {
        this.log('No data to export for session log.', 'info');
      }

    } catch (error) {
      this.log(`Error exporting data: ${error.message}`, 'error');
    }
  }

  async loadEpisodeUrl(url) {
    this.log(`Loading episode: ${url}`);

    try {
      this.startNavigationMonitoring(url);
      await this.page.setCacheEnabled(false);

      await this.page.goto(url, {
        waitUntil: 'networkidle2',
        timeout: this.options.waitTimeout
      });

      this.episodeInfo = await this.page.evaluate(() => {
        return {
          title: document.title.split(' - ')[0] || 'episode',
          showTitle: window.shmotimeVoice?.showTitle || 'show',
          episodeId: window.shmotimeVoice?.shmotimeId || ''
        };
      });

      await this.page.evaluate(() => {
        const originalPushState = history.pushState;
        history.pushState = function() {
          originalPushState.apply(this, arguments);
          console.log(`Navigation detected to: ${arguments[2]}`);
        };

        window.addEventListener('beforeunload', function() {
          console.log('Page navigation or unload detected');
        });

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
    }, 2000);
  }

  getRecordingFilename(extension = 'webm') {
    const date = new Date().toISOString().replace(/[:.]/g, '-');
    const show = (this.episodeInfo?.showTitle || 'show').replace(/[^a-zA-Z0-9]/g, '-');
    const title = (this.episodeInfo?.title || 'episode').replace(/[^a-zA-Z0-9]/g, '-');
    return path.join(this.options.outputDir, `${show}-${title}-${date}.${extension}`);
  }

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

  async initialize() {
    this.log('Initializing browser...');
    fs.mkdirSync(this.options.outputDir, { recursive: true });

    if (this.options.headless && this.options.outputFormat === 'mp4') {
      this.log('MP4 format is often not supported in headless mode, using WebM instead.', 'warn');
      this.options.outputFormat = 'webm';
    }

    const windowWidth = this.options.videoWidth;
    const windowHeight = this.options.videoHeight;

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
      '--enable-gpu-rasterization',
      '--ignore-gpu-blocklist',
      '--use-gl=angle',
      '--enable-accelerated-video-decode',
      '--enable-accelerated-video',
      '--disable-features=AudioServiceOutOfProcess',
      '--force-video-overlays',
      '--enable-features=VaapiVideoDecoder',
      '--disable-features=VizDisplayCompositor',
      `--force-device-scale-factor=1`,
    ];
    
    if (this.options.headless) {
      browserArgs.push(
        '--headless=new',
        '--enable-unsafe-swiftshader',
        '--disable-gpu-sandbox'
      );
    }

    const executablePath = this.options.executablePath || this.getChromePath();
    if (!executablePath) {
      throw new Error('Could not find Chrome executable. Please specify using --chrome-path=');
    }

    this.log(`Using Chrome at: ${executablePath}`);

    this.browser = await launch({
      headless: this.options.headless ? "new" : false,
      args: browserArgs,
      executablePath: executablePath,
      defaultViewport: null
    });  

    this.page = await this.browser.newPage();

    // KEEP the original CDP session setup - this is important!
    const session = await this.page.target().createCDPSession();
    const {windowId} = await session.send('Browser.getWindowForTarget');
    
    const uiSize = await this.page.evaluate(() => {
      return {
        height: window.outerHeight - window.innerHeight,
        width: window.outerWidth - window.innerWidth,
      };
    });
    
    await session.send('Browser.setWindowBounds', {
      windowId,
      bounds: {
        height: windowHeight + uiSize.height,
        width: windowWidth + uiSize.width,
      },
    });
    
    await this.page.setViewport({
      width: windowWidth,
      height: windowHeight,
      deviceScaleFactor: 1
    });
    
    // KEEP the original CSS - it works!
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
        
        #root, main, .app-container, .scene-container, .player-container, 
        [class*="container"], [class*="wrapper"], [class*="player"], [class*="scene"] {
          position: fixed !important;
          top: 0 !important;
          left: 0 !important;
          width: 100% !important;
          height: 100% !important;
          z-index: 1 !important;
        }
        
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
        
        .header-container, header {
          z-index: 0 !important;
        }
      `
    });
    
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
    
    this.page.setDefaultNavigationTimeout(120000);
    this.setupErrorHandling();
    this.log('Browser initialized successfully');
    return this;
  }

  setupErrorHandling() {
    this.page.on('console', async msg => {
      const msgArgs = msg.args();
      if (msgArgs.length === 0) {
        if (this.options.verbose) this.log(`Browser (empty console args): ${msg.text()}`, 'debug');
        return;
      }

      let eventText = '';
      try {
        eventText = await msgArgs[0].jsonValue(); 
      } catch (e) {
        eventText = msg.text(); 
      }
      
      if (typeof eventText !== 'string') {
        if (this.options.verbose) this.log(`Browser (non-string eventText after processing arg[0]): ${msg.text()}`, 'debug');
        eventText = msg.text(); 
        if (typeof eventText !== 'string') {
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

            if (msgArgs.length > 1) {
              try {
                eventData = await msgArgs[1].jsonValue();
              } catch (jsonError) {
                this.log(`Failed to get JSON value for recorder event data (${eventType}): ${jsonError.message}`, 'warn');
                try {
                    const rawDataText = await msgArgs[1].evaluate(arg => {
                        if (arg instanceof Error) return arg.message;
                        if (arg instanceof Object) return JSON.stringify(arg);
                        return String(arg);
                    });
                    this.log(`Raw event data for ${eventType} (fallback): ${rawDataText}`, 'debug');
                    if (typeof rawDataText === 'string' && (rawDataText.startsWith('{') || rawDataText.startsWith('['))) {
                        try { eventData = JSON.parse(rawDataText); } catch (e) { /* ignore parse error */ }
                    }
                } catch (rawDataError) {
                    this.log(`Could not get raw string/JSON for event data ${eventType}: ${rawDataError.message}`, 'debug');
                }
              }
            }
            this.handleRecorderEvent(eventType, eventData);
            return; 
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

    this.page.on('requestfailed', request => {
      const url = request.url();
      if (url.includes('.mp3') || url.includes('.mp4') || url.includes('media') || url.includes('audio')) {
        this.log(`Failed to load media: ${url} - ${request.failure().errorText}`, 'error');
      }
    });

    this.page.on('error', err => {
      this.log(`Page error: ${err.message}`, 'error');
    });

    this.page.on('close', () => {
      this.log('Page was closed');
      this.endDetected = true;
    });
  }

  async startEpisode() {
    this.log('Starting episode playback...');

    try {
      this.log('Waiting for start button...');
      await this.page.waitForFunction((selector) => {
        const slate = document.querySelector(selector);
        return slate && window.getComputedStyle(slate).display !== 'none';
      }, { timeout: this.options.waitTimeout }, this.SLATE_WAIT_SELECTOR);

      let videoFile = null;

      if (this.options.record) {
        const viewportSize = await this.page.evaluate(() => ({
          width: window.innerWidth,
          height: window.innerHeight,
          bodyWidth: document.body.clientWidth,
          bodyHeight: document.body.clientHeight
        }));
        
        this.log(`Pre-recording dimensions check:
          Viewport: ${viewportSize.width}x${viewportSize.height}
          Body: ${viewportSize.bodyWidth}x${viewportSize.bodyHeight}`);
        
        if (viewportSize.height !== this.options.videoHeight || 
            viewportSize.width !== this.options.videoWidth) {
          this.log('Viewport dimensions mismatch - attempting to fix...', 'warn');
          
          await this.page.setViewport({
            width: this.options.videoWidth,
            height: this.options.videoHeight,
            deviceScaleFactor: 1
          });
          
          await this.page.addStyleTag({
            content: `
              html, body {
                margin: 0 !important;
                padding: 0 !important;
                width: ${this.options.videoWidth}px !important;
                height: ${this.options.videoHeight}px !important;
                overflow: hidden !important;
              }
              
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
          
        const filename = this.getRecordingFilename(this.options.outputFormat);
        this.log(`Starting recording: ${filename}`);
        this.outputFile = fs.createWriteStream(filename);

        const mimeType = this.options.outputFormat === 'mp4' ?
          "video/mp4;codecs=avc1,mp4a.40.2" :
          "video/webm;codecs=vp8,opus";

        this.log(`Using codec: ${mimeType}`, 'debug');

        try {
          this.stream = await getStream(this.page, {
            audio: true,
            video: true,
            frameSize: 1000,
            bitsPerSecond: 8000000,
            mimeType: mimeType
          });
          
          videoFile = filename;
        } catch (error) {
          if (this.options.outputFormat === 'mp4' && error.message.includes('not supported')) {
            this.log('MP4 recording failed, falling back to WebM format.', 'warn');
            this.options.outputFormat = 'webm';
        
            if (this.outputFile) {
              this.outputFile.close();
            }
        
            const webmFilename = this.getRecordingFilename('webm');
            this.log(`Switching to WebM recording: ${webmFilename}`);
            this.outputFile = fs.createWriteStream(webmFilename);
        
            this.stream = await getStream(this.page, {
              audio: true,
              video: true,
              frameSize: 1000,
              bitsPerSecond: 6000000,
              mimeType: "video/webm;codecs=vp8,opus"
            });
        
            videoFile = webmFilename;
          } else {
            this.log(`Recording error: ${error.message}`, 'error');
            throw error;
          }
        }  
   
        this.stream.pipe(this.outputFile);
        
        this.log(`Recording started with dimensions ${this.options.videoWidth}x${this.options.videoHeight} @ ${this.options.frameRate}fps`);
        this.log(`Stream settings: frameSize=1000ms, codec=${mimeType}`, 'debug');
        this.log(`FFmpeg will set final frame rate to ${this.options.frameRate}fps during post-processing.`, 'debug');
      }

      this.log('Clicking start button...');
      try {
        const clickResult = await this.page.evaluate(({ slateButtonSelectors, textButtonSelectorsLC, slateContainerSelectors }) => {
          let clicked = false;
          let clickTargetInfo = 'No suitable click targets found';

          // Try specific selectors first
          for (const selector of slateButtonSelectors) {
            const btn = document.querySelector(selector);
            if (btn) {
              try {
                btn.click();
                clicked = true;
                clickTargetInfo = `Clicked button: ${btn.outerHTML.substring(0, 80)}...`;
                break;
              } catch (e) { /* continue */ }
            }
          }

          // Try text-based button search
          if (!clicked) {
            const allButtons = Array.from(document.querySelectorAll('button'));
            for (const btn of allButtons) {
              const btnText = btn.textContent.toLowerCase();
              if (textButtonSelectorsLC.some(txt => btnText.includes(txt))) {
                try {
                  btn.click();
                  clicked = true;
                  clickTargetInfo = `Clicked button (text match): ${btn.outerHTML.substring(0, 80)}...`;
                  break;
                } catch (e) { /* continue */ }
              }
            }
          }

          // Try clicking on common slate areas if no buttons found or clicks failed
          if (!clicked) {
            for (const selector of slateContainerSelectors) {
              const el = document.querySelector(selector);
              if (el) {
                try {
                  el.click();
                  clicked = true;
                  clickTargetInfo = `Clicked slate element: ${el.outerHTML.substring(0, 80)}...`;
                  break;
                } catch (e) { /* continue */ }
              }
            }
          }
          return clickTargetInfo;
        }, { slateButtonSelectors: this.SLATE_BUTTON_SELECTORS, textButtonSelectorsLC: this.TEXT_BUTTON_SELECTORS_LOWERCASE, slateContainerSelectors: this.SLATE_CONTAINER_SELECTORS });
        
        this.log(`Click result: ${clickResult}`);
      } catch (error) {
        this.log(`Direct click evaluation failed: ${error.message}`, 'warn');
        // Fallback click using Puppeteer's direct click on combined selectors if evaluate fails
        try {
          await this.page.click(this.SLATE_BUTTON_SELECTORS.join(', '));
          this.log('Fallback click succeeded on primary selectors');
        } catch (clickError) {
          this.log(`All click attempts failed - episode may not start properly: ${clickError.message}`, 'error');
        }
      }

      this.log('Waiting for scene to load...');
      try {
        await this.page.waitForFunction((selectors) => {
          return (
            document.querySelector(selectors.slate)?.style.display === 'none' ||
            selectors.dialogue.some(sel => document.querySelector(sel)?.textContent !== '')
          );
        }, { timeout: this.options.waitTimeout }, { slate: this.SLATE_WAIT_SELECTOR, dialogue: this.DIALOGUE_TEXT_SELECTORS });
        this.log('Scene loaded successfully');
      } catch (error) {
        this.log('Could not detect scene load, continuing anyway...', 'warn');
      }

      await this.ensureAudioEnabled();
      this.log('Episode playback started');
      return { videoFile };
    } catch (error) {
      this.log(`Error starting episode: ${error.message}`, 'error');
      return { videoFile: null };
    }
  }

  async ensureAudioEnabled() {
    await this.page.evaluate(() => {
      function enableAudio() {
        document.querySelectorAll('audio, video').forEach(el => {
          if (el.paused) {
            el.play().catch(() => {});
          }
          el.muted = false;
          el.volume = 1;
        });

        const speakerAudio = document.getElementById('speaker-audio');
        if (speakerAudio) {
          if (speakerAudio.paused) {
            speakerAudio.play().catch(() => {});
          }
          speakerAudio.muted = false;
          speakerAudio.volume = 1;
        }

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

      enableAudio();
      setTimeout(enableAudio, 1000);
      setTimeout(enableAudio, 3000);
    });
  }

  async waitForEpisodeToFinish(timeout = 3600000) {
    this.log(`Waiting for episode to finish using recorder events (timeout: ${timeout}ms)...`);

    const startTime = Date.now();
    let statusInterval;

    try {
      this.endDetected = false;
      
      statusInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        this.log(`Still waiting... (${Math.floor(elapsed / 60)}m ${elapsed % 60}s elapsed) - Current phase: ${this.currentPhase}`);
        
        const recentEvents = this.recorderEvents.slice(-3).map(e => e.type).join(', ');
        if (recentEvents) {
          this.log(`Recent events: ${recentEvents}`, 'debug');
        }
      }, 30000);

      while (!this.endDetected && (Date.now() - startTime) < timeout) {
        if (this.currentPhase === 'ended') {
          this.log('Episode ended detected through phase tracking');
          this.endDetected = true;
          break;
        }
        
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      if (statusInterval) {
        clearInterval(statusInterval);
        statusInterval = null;
      }

      if (!this.endDetected) {
        this.log('Episode wait timeout reached', 'warn');
      }

      await new Promise(r => setTimeout(r, 2000));
      return this.endDetected;
    } catch (error) {
      this.log(`Error waiting for episode to finish: ${error.message}`, 'error');
      if (statusInterval) {
        clearInterval(statusInterval);
      }
      return false;
    } finally {
      if (this.navigationMonitor) {
        clearInterval(this.navigationMonitor);
        this.navigationMonitor = null;
      }
    }
  }

  async close() {
    this.log('Cleaning up resources...');

    await this.exportProcessedData();

    if (this.navigationMonitor) {
      clearInterval(this.navigationMonitor);
      this.navigationMonitor = null;
    }

    if (this.stream && !this.recordingStopped) {
      await this.stopRecording();
    }

    if (this.browser && !this.browser.process()?.killed) {
      try {
        await this.browser.close();
        this.log('Browser closed');
      } catch (error) {
        this.log(`Error closing browser: ${error.message}`, 'error');
      }
    }

    try {
      if (wss) (await wss).close();
      this.log('WebSocket server closed');
    } catch (error) {
      this.log(`Error closing WebSocket server: ${error.message}`, 'error');
    }

    this.log(`Session complete: ${this.recorderEvents.length} events recorded`);
    if (this.showConfig) {
      this.log(`Show: ${this.showConfig.id} (${Object.keys(this.showConfig.actors).length} actors)`);
    }
    if (this.episodeData) {
      this.log(`Episode: ${this.episodeData.id} (${this.episodeData.scenes.length} scenes)`);
    }

    this.log('All resources cleaned up');
  } 
}

// Command line interface - simplified but keeping all functionality
function parseArgs() {
  const args = process.argv.slice(2);
  
  if (args.includes('--help') || args.length === 0) {
    console.log(`
Usage: node recorder.js [options] <url>

Options:
  --headless                    Run in headless mode
  --no-record                   Disable video recording
  --no-export                   Disable data export
  --no-fix-framerate            Disable ffmpeg frame rate post-processing
  --quiet                       Reduce log output
  --wait=<ms>                   Maximum wait time (default: 3600000)
  --output=<dir>                Output directory (default: ./recordings)
  --chrome-path=<path>          Chrome executable path
  --format=<format>             Video format: mp4 or webm (default: mp4)
  --stop-recording-at=<event>   When to stop recording (default: end_credits)
                                Options: end_ep, end_credits, end_postcredits
  --height=<pixels>             Video height (default: 1080)
  --width=<pixels>              Video width (default: 1920)
  --fps=<number>                Frame rate (default: 30)
  --help                        Show this help
`);
    process.exit(0);
  }

  const headless = args.includes('--headless');
  const noRecord = args.includes('--no-record');
  const noExport = args.includes('--no-export');
  const noFixFrameRate = args.includes('--no-fix-framerate');
  const verbose = !args.includes('--quiet');
  const url = args.find(arg => !arg.startsWith('--')) || 'https://shmotime.com/shmotime_episode/the-security-sentinel/';
  const waitTime = parseInt(args.find(arg => arg.startsWith('--wait='))?.split('=')[1] || '3600000', 10);
  const outputDir = args.find(arg => arg.startsWith('--output='))?.split('=')[1] || './recordings';
  const chromePath = args.find(arg => arg.startsWith('--chrome-path='))?.split('=')[1] || '';
  const outputFormat = args.find(arg => arg.startsWith('--format='))?.split('=')[1] || 'mp4';
  const stopRecordingAt = args.find(arg => arg.startsWith('--stop-recording-at='))?.split('=')[1] || 'end_credits';
  const viewportHeight = parseInt(args.find(arg => arg.startsWith('--height='))?.split('=')[1] || '1080', 10);
  const viewportWidth = parseInt(args.find(arg => arg.startsWith('--width='))?.split('=')[1] || '1920', 10);
  const frameRate = parseInt(args.find(arg => arg.startsWith('--fps='))?.split('=')[1] || '30', 10);

  const validStopEvents = ['end_ep', 'end_credits', 'end_postcredits'];
  if (!validStopEvents.includes(stopRecordingAt)) {
    console.error(`Invalid --stop-recording-at value: ${stopRecordingAt}`);
    console.error(`Valid options: ${validStopEvents.join(', ')}`);
    process.exit(1);
  }

  return {
    url,
    options: {
      headless,
      record: !noRecord,
      exportData: !noExport,
      fixFrameRate: !noFixFrameRate,
      verbose,
      outputDir,
      waitTimeout: 60000,
      executablePath: chromePath,
      outputFormat,
      stopRecordingAt,
      videoWidth: viewportWidth,
      videoHeight: viewportHeight,
      frameRate
    },
    waitTime
  };
}

async function main() {
  const { url, options, waitTime } = parseArgs();
  
  console.log('Shmotime Player V2 starting...');
  console.log(`URL: ${url}`);
  console.log(`Settings: headless=${options.headless}, record=${options.record}, export=${options.exportData}, format=${options.outputFormat}, verbose=${options.verbose}`);
  console.log(`Recording: stop at ${options.stopRecordingAt}`);
  console.log(`Video: ${options.videoWidth}x${options.videoHeight}@${options.frameRate}fps`);

  const player = new ShmotimeRecorder(options);

  try {
    await player.initialize();

    const episodeInfo = await player.loadEpisodeUrl(url);
    if (!episodeInfo) {
      throw new Error('Failed to load episode');
    }

    const { videoFile } = await player.startEpisode();
    if (!videoFile && options.record) {
      throw new Error('Failed to start episode recording');
    }

    await player.waitForEpisodeToFinish(waitTime);

    console.log('Episode processing complete');
    if (videoFile) console.log(`Video will be saved to: ${videoFile}`);

  } catch (error) {
    console.error(`Main process error: ${error.message}`);
  } finally {
    await player.close();
    console.log('Process complete');
    process.exit(0);
  }
}

if (require.main === module) {
  main().catch(error => {
    console.error(`Fatal error: ${error.message}`);
    process.exit(1);
  });
}

module.exports = ShmotimeRecorder;
