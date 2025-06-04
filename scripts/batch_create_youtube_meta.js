const fs = require('fs');
const path = require('path');

const OLD_RECORDINGS_DIR = path.join(__dirname, '..', 'recordings', 'old');
const OUTPUT_DIR = path.join(__dirname, '..', 'recordings');
const THUMBNAIL_PATH = path.join(__dirname, '..', 'media', 'logos', 'logo.png');

function extractEpisodeName(filename) {
  // Extract episode name from JedAI-Council-Episode-Name.mp4
  const match = filename.match(/^JedAI-Council-(.+)\.mp4$/);
  return match ? match[1] : null;
}

function formatEpisodeTitle(episodeName) {
  // Convert hyphenated name to proper title
  // "The-Governance-Dilemma" -> "The Governance Dilemma"
  return episodeName.replace(/-/g, ' ').replace(/--/g, ' - ');
}

function getEpisodeDate(episodeId) {
  // S1E1 = 2025-05-27, S1E2 = 2025-05-28, etc.
  const match = episodeId.match(/S1E(\d+)/);
  if (!match) return '2025-06-02'; // fallback
  
  const episodeNum = parseInt(match[1]);
  const baseDate = new Date('2025-05-27');
  baseDate.setDate(baseDate.getDate() + (episodeNum - 1));
  
  return baseDate.toISOString().split('T')[0];
}

function normalizeTitle(title) {
  // Normalize titles for comparison by removing/standardizing punctuation and spacing
  return title
    .replace(/[\.,:;]/g, '') // Remove periods, commas, colons, semicolons
    .replace(/--+/g, ' ')    // Convert double dashes to spaces
    .replace(/\s+/g, ' ')    // Normalize multiple spaces to single space
    .replace(/-/g, ' ')      // Convert remaining hyphens to spaces
    .toLowerCase()
    .trim();
}

function findMatchingEpisodeData(mp4File, allEventFiles) {
  // Extract episode name from MP4 filename for comparison
  const episodeName = extractEpisodeName(mp4File);
  if (!episodeName) return null;
  
  // Convert episode name to a comparable format
  const episodeNameFormatted = formatEpisodeTitle(episodeName);
  const episodeNameNormalized = normalizeTitle(episodeNameFormatted);
  
  // Try each event file to find matching episode data
  for (const eventFile of allEventFiles) {
    try {
      const eventPath = path.join(OLD_RECORDINGS_DIR, eventFile);
      const eventContent = fs.readFileSync(eventPath, 'utf-8');
      const eventData = JSON.parse(eventContent);
      
      // Look for load_episode event in the events array
      if (eventData.events && Array.isArray(eventData.events)) {
        const loadEpisodeEvent = eventData.events.find(event => event.type === 'load_episode');
        
        if (loadEpisodeEvent && loadEpisodeEvent.data && loadEpisodeEvent.data.title && loadEpisodeEvent.data.premise) {
          const eventEpisodeTitle = loadEpisodeEvent.data.title;
          const eventTitleNormalized = normalizeTitle(eventEpisodeTitle);
          
          // Compare the normalized titles
          if (eventTitleNormalized === episodeNameNormalized) {
            console.log(`    Found episode data match: "${eventEpisodeTitle}" (${loadEpisodeEvent.data.id}) in ${eventFile}`);
            return {
              ...loadEpisodeEvent.data,
              episodeId: loadEpisodeEvent.data.id
            };
          }
        }
      }
    } catch (e) {
      console.warn(`    Could not read ${eventFile}: ${e.message}`);
    }
  }
  
  console.warn(`    No episode data found matching "${episodeNameFormatted}" (normalized: "${episodeNameNormalized}")`);
  return null;
}

function generateDescription(episodeTitle, episodeDate, premise) {
  const basePremise = premise || "The JedAI Council convenes to discuss the latest developments in AI, blockchain, and decentralized governance.";
  
  return `Recorded: ${episodeDate}

${basePremise}

This episode of JedAI Council features AI agents debating and exploring the intersection of artificial intelligence, blockchain technology, and decentralized governance.

https://m3org.com/tv/jedai-council
https://github.com/elizaOS/knowledge
`;
}

async function processRecordings() {
  console.log(`Scanning for MP4 files in: ${OLD_RECORDINGS_DIR}`);
  console.log(`Outputting YouTube meta JSONs to: ${OUTPUT_DIR}`);
  console.log(`Using thumbnail: ${THUMBNAIL_PATH}`);

  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  // Check if thumbnail exists
  const thumbnailExists = fs.existsSync(THUMBNAIL_PATH);
  if (!thumbnailExists) {
    console.warn(`WARNING: Thumbnail file not found at ${THUMBNAIL_PATH}`);
  }

  let oldFiles;
  try {
    oldFiles = fs.readdirSync(OLD_RECORDINGS_DIR);
  } catch (error) {
    console.error(`Error reading directory ${OLD_RECORDINGS_DIR}:`, error);
    return;
  }

  const mp4Files = oldFiles.filter(f => f.startsWith('JedAI-Council-') && f.endsWith('.mp4'));
  const eventFiles = oldFiles.filter(f => f.match(/^S\d+E\d+-events-.*\.json$/));

  if (mp4Files.length === 0) {
    console.log('No JedAI-Council MP4 files found to process.');
    return;
  }

  console.log(`Found ${mp4Files.length} JedAI-Council MP4 files and ${eventFiles.length} event JSON files.`);

  let createdCount = 0;
  for (const mp4File of mp4Files) {
    console.log(`\nProcessing: ${mp4File}`);
    
    const episodeName = extractEpisodeName(mp4File);
    if (!episodeName) {
      console.warn(`  Could not extract episode name from: ${mp4File}`);
      continue;
    }

    const episodeTitle = formatEpisodeTitle(episodeName);
    
    // Find matching episode data
    const episodeData = findMatchingEpisodeData(mp4File, eventFiles);
    if (!episodeData) {
      console.warn(`  Skipping ${mp4File} - no matching episode data found`);
      continue;
    }
    
    const episodeId = episodeData.episodeId;
    const premise = episodeData.premise;
    const episodeDate = getEpisodeDate(episodeId);
    
    const youtubeTitle = `JedAI Council: ${episodeTitle}`;
    const description = generateDescription(episodeTitle, episodeDate, premise);
    
    console.log(`  Episode ID: ${episodeId}`);
    console.log(`  Episode: ${episodeTitle}`);
    console.log(`  Recording Date: ${episodeDate}`);
    console.log(`  Premise: ${premise ? premise.substring(0, 80) + '...' : 'Using default premise'}`);
    console.log(`  YouTube Title: ${youtubeTitle}`);

    const youtubeMetaData = {
      video_file: path.join('recordings', 'old', mp4File),
      title: youtubeTitle,
      description: description,
      tags: 'JedAI Council,AI,Blockchain,Web3,Podcast,Shmotime,Governance,Intelligence',
      category_id: '22',
      privacy_status: 'private'
    };

    // Add thumbnail if it exists
    if (thumbnailExists) {
      youtubeMetaData.thumbnail_file = 'media/logos/logo.png';
    }

    // Use episode ID for filename
    const outputJsonFileName = `${episodeId}_youtube-meta.json`;
    const outputJsonPath = path.join(OUTPUT_DIR, outputJsonFileName);

    try {
      fs.writeFileSync(outputJsonPath, JSON.stringify(youtubeMetaData, null, 2));
      console.log(`  SUCCESS: Created ${outputJsonFileName}`);
      createdCount++;
    } catch (writeError) {
      console.error(`  ERROR: Could not write ${outputJsonFileName}:`, writeError);
    }
  }
  
  console.log(`\nBatch processing complete. Created ${createdCount} YouTube metadata JSON files.`);
  if (thumbnailExists) {
    console.log(`All files include thumbnail: ${THUMBNAIL_PATH}`);
  }
}

processRecordings().catch(console.error); 