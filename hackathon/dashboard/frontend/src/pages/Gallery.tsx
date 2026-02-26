import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { ChevronLeft, ChevronRight, X, Camera } from 'lucide-react';

// Gallery filenames - curated media assets and behind-the-scenes dev shots
const GALLERY_FILENAMES = [
  '9504cf75-1b14-4f28-8043-903cb958f194.jpg',
  'arbitrum.jpeg',
  'chatgpt_image_may_29_2025_10_15_43_pm.jpg',
  'clanktank-set.jpg',
  'clanktank.jpg',
  'clanktank1.jpg',
  'clanktank2.jpg',
  'clanktank3.jpg',
  'clanktank5.jpg',
  'eliza_cover.jpeg',
  'f0b461ea-106d-404e-96c3-1686cfe552a4.jpg',
  'just_mary.jpeg',
  'mary_and_eliza.jpeg',
  'montage-x23-vrm.jpg',
  'mpv-shot1037.jpg',
  'mpv-shot1039.jpg',
  'mpv-shot1040.jpg',
  'mpv-shot1041.jpg',
  'mpv-shot1043.jpg',
  'mpv-shot1044.jpg',
  'mpv-shot1094.jpg',
  'mpv-shot1095.jpg',
  'mpv-shot1102.jpg',
  'mpv-shot1103.jpg',
  'mpv-shot1104.jpg',
  'mpv-shot1116.jpg',
  'mpv-shot1119.jpg',
  'mpv-shot1121.jpg',
  'mpv-shot1178.jpg',
  'mpv-shot1200.jpg',
  'mpv-shot1216.jpg',
  'optimism.jpeg',
  'optimism_judges.jpeg',
  'screenshot-from-2025-01-16-12-51-34.jpg',
  'screenshot-from-2025-01-20-23-35-51.jpg',
  'screenshot-from-2025-01-23-18-35-34.jpg',
  'screenshot-from-2025-01-23-18-37-26.jpg',
  'screenshot-from-2025-01-24-20-07-21.jpg',
  'screenshot-from-2025-01-29-09-34-43.jpg',
  'screenshot-from-2025-02-04-17-44-53.jpg',
  'screenshot-from-2025-02-04-17-45-04.jpg',
  'screenshot-from-2025-02-04-18-54-31.jpg',
  'screenshot-from-2025-02-04-21-20-13.jpg',
  'screenshot-from-2025-02-04-21-32-26.jpg',
  'screenshot-from-2025-02-04-21-54-38.jpg',
  'screenshot-from-2025-02-07-17-11-41.jpg',
  'screenshot-from-2025-02-07-17-11-47.jpg',
  'screenshot-from-2025-02-13-10-28-10.jpg',
  'screenshot-from-2025-02-13-10-49-45.jpg',
  'screenshot-from-2025-02-15-12-59-41.jpg',
  'screenshot-from-2025-02-15-13-01-18.jpg',
  'screenshot-from-2025-02-20-10-35-22.jpg',
  'screenshot-from-2025-02-20-17-02-15.jpg',
  'screenshot-from-2025-02-23-13-51-13.jpg',
  'screenshot-from-2025-02-26-11-25-02.jpg',
  'screenshot-from-2025-02-26-15-55-23.jpg',
  'screenshot-from-2025-02-26-16-02-09.jpg',
  'screenshot-from-2025-03-02-13-11-09.jpg',
  'screenshot-from-2025-03-07-17-59-39.jpg',
  'screenshot-from-2025-03-15-22-27-38.jpg',
  'screenshot-from-2025-03-15-22-28-39.jpg',
  'screenshot-from-2025-04-03-17-57-46.jpg',
  'screenshot-from-2025-04-03-17-57-59.jpg',
  'screenshot-from-2025-04-04-11-20-27.jpg',
  'screenshot-from-2025-04-04-11-20-52.jpg',
  'screenshot-from-2025-04-04-11-20-57.jpg',
  'screenshot-from-2025-04-04-11-21-34.jpg',
  'screenshot-from-2025-04-04-19-07-14.jpg',
  'screenshot-from-2025-04-07-20-22-18.jpg',
  'screenshot-from-2025-04-08-18-27-13.jpg',
  'screenshot-from-2025-04-08-18-39-59.jpg',
  'screenshot-from-2025-04-08-18-40-06.jpg',
  'screenshot-from-2025-04-08-18-40-09.jpg',
  'screenshot-from-2025-04-08-18-40-31.jpg',
  'screenshot-from-2025-04-08-18-40-42.jpg',
  'screenshot-from-2025-04-08-18-40-48.jpg',
  'screenshot-from-2025-04-08-18-41-20.jpg',
  'screenshot-from-2025-04-08-18-42-20.jpg',
  'screenshot-from-2025-04-08-18-44-16.jpg',
  'screenshot-from-2025-04-08-18-45-23.jpg',
  'screenshot-from-2025-04-08-21-40-24.jpg',
  'screenshot-from-2025-05-02-20-00-25.jpg',
  'screenshot-from-2025-05-03-20-05-00.jpg',
  'screenshot-from-2025-05-07-16-17-53.jpg',
  'screenshot-from-2025-05-11-16-06-29.jpg',
  'screenshot-from-2025-05-16-15-47-33.jpg',
  'screenshot-from-2025-05-30-21-23-07.jpg',
  'screenshot-from-2025-07-01-21-00-51.jpg',
  'screenshot-from-2025-07-03-16-01-04.jpg',
  'screenshot-from-2025-07-03-16-10-04.jpg',
  'screenshot-from-2025-07-03-16-11-59.jpg',
  'screenshot-from-2025-07-03-17-03-25.jpg',
  'screenshot-from-2025-07-07-13-00-32.jpg',
  'screenshot-from-2025-07-08-14-34-32.jpg',
  'screenshot-from-2025-07-18-21-16-33.jpg',
  'screenshot-from-2025-07-18-21-17-15.jpg',
  'screenshot-from-2025-07-18-21-20-14.jpg',
  'whales30006.jpeg',
];

// Memoized gallery images to prevent recreation
const createGalleryImages = () => GALLERY_FILENAMES.map(filename => ({
  filename,
  path: `${import.meta.env.BASE_URL}media/${filename}`,
}));

export default function Gallery() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [touchStart, setTouchStart] = useState(0);
  const [touchEnd, setTouchEnd] = useState(0);
  
  // Memoize gallery images to prevent recreation on every render
  const galleryImages = useMemo(() => createGalleryImages(), []);

  // Update meta tags for gallery page
  useEffect(() => {
    const originalTitle = document.title;
    const originalDescription = document.querySelector('meta[name="description"]')?.getAttribute('content') || '';
    const originalOgTitle = document.querySelector('meta[property="og:title"]')?.getAttribute('content') || '';
    const originalOgDescription = document.querySelector('meta[property="og:description"]')?.getAttribute('content') || '';
    const originalOgImage = document.querySelector('meta[property="og:image"]')?.getAttribute('content') || '';
    const originalTwitterTitle = document.querySelector('meta[property="twitter:title"]')?.getAttribute('content') || '';
    const originalTwitterDescription = document.querySelector('meta[property="twitter:description"]')?.getAttribute('content') || '';
    const originalTwitterImage = document.querySelector('meta[property="twitter:image"]')?.getAttribute('content') || '';

    // Gallery page meta data
    const galleryTitle = 'Clank Tank Dev Gallery';
    const galleryDescription = 'Visual journey through Clank Tank\'s development.';
    const galleryImage = `${import.meta.env.BASE_URL}media/clanktank-set.jpg`; // Use a representative image

    // Update meta tags
    document.title = galleryTitle;
    
    const updateMetaContent = (selector: string, content: string) => {
      const meta = document.querySelector(selector);
      if (meta) meta.setAttribute('content', content);
    };

    updateMetaContent('meta[name="description"]', galleryDescription);
    updateMetaContent('meta[property="og:title"]', galleryTitle);
    updateMetaContent('meta[property="og:description"]', galleryDescription);
    updateMetaContent('meta[property="og:image"]', galleryImage);
    updateMetaContent('meta[property="twitter:title"]', galleryTitle);
    updateMetaContent('meta[property="twitter:description"]', galleryDescription);
    updateMetaContent('meta[property="twitter:image"]', galleryImage);

    // Cleanup function to restore original meta tags
    return () => {
      document.title = originalTitle;
      updateMetaContent('meta[name="description"]', originalDescription);
      updateMetaContent('meta[property="og:title"]', originalOgTitle);
      updateMetaContent('meta[property="og:description"]', originalOgDescription);
      updateMetaContent('meta[property="og:image"]', originalOgImage);
      updateMetaContent('meta[property="twitter:title"]', originalTwitterTitle);
      updateMetaContent('meta[property="twitter:description"]', originalTwitterDescription);
      updateMetaContent('meta[property="twitter:image"]', originalTwitterImage);
    };
  }, []);

  // Navigation functions
  const getCurrentImageIndex = useCallback(() => {
    return galleryImages.findIndex(img => img.path === selectedImage);
  }, [galleryImages, selectedImage]);

  const navigateToImage = useCallback((index: number) => {
    if (index >= 0 && index < galleryImages.length) {
      setSelectedImage(galleryImages[index].path);
    }
  }, [galleryImages]);

  const goToPreviousImage = useCallback(() => {
    const currentIndex = getCurrentImageIndex();
    if (currentIndex > 0) {
      navigateToImage(currentIndex - 1);
    }
  }, [getCurrentImageIndex, navigateToImage]);

  const goToNextImage = useCallback(() => {
    const currentIndex = getCurrentImageIndex();
    if (currentIndex < galleryImages.length - 1) {
      navigateToImage(currentIndex + 1);
    }
  }, [getCurrentImageIndex, navigateToImage, galleryImages.length]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (!selectedImage) return;
      
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        goToPreviousImage();
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        goToNextImage();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        setSelectedImage(null);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [selectedImage, goToPreviousImage, goToNextImage]);

  // Touch handlers for swipe
  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchStart(e.targetTouches[0].clientX);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const handleTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > 50;
    const isRightSwipe = distance < -50;

    if (isLeftSwipe) {
      goToNextImage();
    } else if (isRightSwipe) {
      goToPreviousImage();
    }

    setTouchStart(0);
    setTouchEnd(0);
  };

  // Extract date from screenshot filenames
  const extractDate = (filename: string) => {
    const match = filename.match(/(\d{4}-\d{2}-\d{2})/);
    if (match) {
      return new Date(match[1]).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    }
    return null;
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-gray-50 to-slate-100 dark:from-slate-900 dark:via-slate-850 dark:to-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Camera className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-gray-100">
              Development Gallery
            </h1>
          </div>
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            The evolution of Clank Tank - a visual journey through the development process.
          </p>
        </div>

        {/* Mosaic Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-2 md:gap-3">
          {galleryImages.map((image, index) => {
            // Create variety in grid item sizes for mosaic effect
            const isLarge = (index % 7 === 0 || index % 11 === 0) && index > 0;
            const isTall = (index % 13 === 0) && index > 0;
            
            return (
              <div
                key={image.path}
                className={`relative group cursor-pointer overflow-hidden rounded-lg shadow-md hover:shadow-xl transition-all duration-300 hover:scale-[1.02] ${
                  isLarge ? 'md:col-span-2 md:row-span-2' : ''
                } ${
                  isTall && !isLarge ? 'row-span-2' : ''
                }`}
                onClick={() => setSelectedImage(image.path)}
              >
                <div className={`relative ${isLarge ? 'aspect-square' : isTall ? 'aspect-[3/4]' : 'aspect-square'} bg-gray-200 dark:bg-gray-800`}>
                  <img
                    src={image.path}
                    alt={`Gallery image ${index + 1}`}
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                    loading="lazy"
                  />
                  
                  {/* Simple hover overlay */}
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors duration-200"></div>
                </div>
              </div>
            );
          })}
        </div>

      </div>

      {/* Lightbox */}
      {selectedImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-90"
          onClick={() => setSelectedImage(null)}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
        >
          {/* Navigation Arrows */}
          {getCurrentImageIndex() > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                goToPreviousImage();
              }}
              className="absolute left-2 md:left-4 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 hover:bg-opacity-70 text-white p-2 md:p-3 rounded-full transition-all duration-200 z-10"
              aria-label="Previous image"
            >
              <ChevronLeft className="w-5 h-5 md:w-6 md:h-6" />
            </button>
          )}
          
          {getCurrentImageIndex() < galleryImages.length - 1 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                goToNextImage();
              }}
              className="absolute right-2 md:right-4 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 hover:bg-opacity-70 text-white p-2 md:p-3 rounded-full transition-all duration-200 z-10"
              aria-label="Next image"
            >
              <ChevronRight className="w-5 h-5 md:w-6 md:h-6" />
            </button>
          )}

          <div
            className="relative max-w-[95vw] max-h-[95vh] mx-2 md:mx-0"
            onClick={e => e.stopPropagation()}
          >
            {/* Close Button */}
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute top-2 right-2 text-white bg-black bg-opacity-50 rounded-full w-10 h-10 flex items-center justify-center hover:bg-opacity-70 transition z-10"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Image Counter */}
            <div className="absolute top-2 left-2 bg-black bg-opacity-50 text-white text-xs px-2 py-1 rounded z-10">
              {getCurrentImageIndex() + 1} of {galleryImages.length}
            </div>

            {/* Main Image */}
            <img
              src={selectedImage}
              alt="Gallery image"
              className="max-w-full max-h-full object-contain rounded-lg"
            />

            {/* Image Info */}
            {(() => {
              const currentImage = galleryImages.find(img => img.path === selectedImage);
              const date = currentImage ? extractDate(currentImage.filename) : null;
              
              return date ? (
                <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-50 text-white px-3 py-2 rounded text-center">
                  <div className="text-xs text-gray-300">
                    Captured: {date}
                  </div>
                </div>
              ) : null;
            })()}

            {/* Keyboard Hint */}
            <div className="hidden md:block absolute -bottom-12 left-1/2 transform -translate-x-1/2 text-gray-400 text-xs text-center">
              <div className="flex items-center gap-2">
                <kbd className="px-2 py-1 bg-gray-800 rounded border text-xs">←</kbd>
                <span>Previous</span>
                <kbd className="px-2 py-1 bg-gray-800 rounded border text-xs">→</kbd>
                <span>Next</span>
                <kbd className="px-2 py-1 bg-gray-800 rounded border text-xs">ESC</kbd>
                <span>Close</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}