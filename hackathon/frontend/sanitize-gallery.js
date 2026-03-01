#!/usr/bin/env node

import fs from 'fs';
import path from 'path';

const galleryDir = './public/gallery';

function sanitizeFilename(filename) {
  const ext = path.extname(filename).toLowerCase();
  const basename = path.basename(filename, path.extname(filename));
  
  // Convert to lowercase and replace problematic characters
  let sanitized = basename
    .toLowerCase()
    .replace(/\s+/g, '-')           // spaces to dashes
    .replace(/[^a-z0-9\-_]/g, '')   // remove special chars except dashes and underscores
    .replace(/-+/g, '-')            // multiple dashes to single
    .replace(/^-|-$/g, '');         // remove leading/trailing dashes
  
  return sanitized + ext;
}

function sanitizeGalleryFilenames() {
  if (!fs.existsSync(galleryDir)) {
    console.error('Gallery directory does not exist:', galleryDir);
    return;
  }

  const files = fs.readdirSync(galleryDir);
  const imageFiles = files.filter(file => 
    /\.(jpg|jpeg|png|gif|webp)$/i.test(file)
  );

  console.log(`Found ${imageFiles.length} image files to process...\n`);

  const renames = [];
  
  imageFiles.forEach(filename => {
    const sanitized = sanitizeFilename(filename);
    if (filename !== sanitized) {
      const oldPath = path.join(galleryDir, filename);
      const newPath = path.join(galleryDir, sanitized);
      
      // Check if target already exists
      if (fs.existsSync(newPath)) {
        console.log(`⚠️  Skipping ${filename} -> ${sanitized} (target exists)`);
        return;
      }
      
      renames.push({ old: filename, new: sanitized, oldPath, newPath });
      console.log(`📝 ${filename} -> ${sanitized}`);
    }
  });

  if (renames.length === 0) {
    console.log('✅ All filenames are already sanitized!');
    return;
  }

  console.log(`\n${renames.length} files need renaming. Proceed? (y/N)`);
  
  process.stdin.setRawMode(true);
  process.stdin.resume();
  process.stdin.on('data', (key) => {
    const input = key.toString().toLowerCase();
    
    if (input === 'y') {
      console.log('\n🔄 Renaming files...');
      
      renames.forEach(({ old, new: newName, oldPath, newPath }) => {
        try {
          fs.renameSync(oldPath, newPath);
          console.log(`✅ ${old} -> ${newName}`);
        } catch (error) {
          console.error(`❌ Failed to rename ${old}:`, error.message);
        }
      });
      
      console.log(`\n🎉 Completed! ${renames.length} files renamed.`);
    } else {
      console.log('\n❌ Cancelled.');
    }
    
    process.exit(0);
  });
}

sanitizeGalleryFilenames();