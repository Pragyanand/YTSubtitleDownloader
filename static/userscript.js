// ==UserScript==
// @name         YouTube Auto Transcript Opener & Downloader (Fixed)
// @namespace    http://tampermonkey.net/
// @version      3.1
// @description  Open transcript panel and download transcript as text file. PREVENTS DUPLICATES.
// @match        https://www.youtube.com/watch*
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    let lastVideoId = null;
    let attempts = 0;
    const maxAttempts = 15;

    // --- HELPER: LOGGING ---
    // We use a prefix to easily spot our logs
    function log(msg) {
        console.log(`[YT-Subs-Bot] ${msg}`);
    }

    function getVideoId() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('v');
    }

    function getVideoTitle() {
        const titleElement = document.querySelector('h1.ytd-video-primary-info-renderer yt-formatted-string, h1.style-scope.ytd-watch-metadata');
        return titleElement ? titleElement.textContent.trim() : 'transcript';
    }

    function sanitizeFileName(name) {
        return name.replace(/[\\/:*?"<>|]/g, '_').substring(0, 200);
    }

    function isTranscriptOpen() {
        const transcriptBtn = document.querySelector('button[aria-label*="transcript"]');
        return transcriptBtn && transcriptBtn.getAttribute('aria-label').includes('Hide'); // If it says "Hide transcript", it's is open.
    }

    // --- FIX: CHECK IF ALREADY DOWNLOADED ---
    function hasAlreadyDownloaded(videoId) {
        return sessionStorage.getItem('subs_downloaded_' + videoId) === 'true';
    }

    function markAsDownloaded(videoId) {
        sessionStorage.setItem('subs_downloaded_' + videoId, 'true');
    }

    // --- API REPORTING ---
    function reportToLocalServer(videoId, title, status, message) {
        // Try to report to localhost
        // Use GM_xmlhttpRequest if available, otherwise fetch
        const data = {
            videoId: videoId,
            title: title,
            status: status,
            message: message
        };

        fetch('http://localhost:5000/api/log', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
            .then(response => console.log('Reported to server:', response.status))
            .catch(error => console.log('Failed to report to server:', error));
    }

    function extractAndDownloadTranscript() {
        const currentVideoId = getVideoId();
        const videoTitle = getVideoTitle();

        // Double check before downloading
        if (hasAlreadyDownloaded(currentVideoId)) {
            log('Already downloaded this session. Skipping.');
            return true; // Return true so we stop trying
        }

        const container = document.querySelector('#segments-container');

        if (!container) {
            log('Transcript container not found yet...');
            return false;
        }

        const segments = container.querySelectorAll('ytd-transcript-segment-renderer');

        if (segments.length === 0) {
            log('No transcript segments found yet...');
            return false;
        }

        let transcriptText = '';

        segments.forEach(segment => {
            const textElement = segment.querySelector('.segment-text');
            if (textElement) {
                transcriptText += textElement.textContent.trim() + ' ';
            }
        });

        if (transcriptText.trim().length === 0) {
            return false;
        }

        // Create and download the file
        const fileName = sanitizeFileName(videoTitle) + '_transcript.txt';

        const blob = new Blob([transcriptText.trim()], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        log('Transcript downloaded: ' + fileName);

        // --- MARK AS DONE & REPORT ---
        markAsDownloaded(currentVideoId);
        reportToLocalServer(currentVideoId, videoTitle, 'SUCCESS', 'Downloaded ' + fileName);

        return true;
    }

    function waitForTranscriptAndDownload() {
        let downloadAttempts = 0;
        const maxDownloadAttempts = 20;

        const checkInterval = setInterval(() => {
            downloadAttempts++;

            // Abort if ID changed mid-process
            if (getVideoId() !== lastVideoId) {
                clearInterval(checkInterval);
                return;
            }

            if (extractAndDownloadTranscript()) {
                clearInterval(checkInterval);
            } else if (downloadAttempts >= maxDownloadAttempts) {
                log('Could not extract transcript after maximum attempts');
                reportToLocalServer(getVideoId(), getVideoTitle(), 'FAILED', 'Transcript not found or empty after timeout');
                clearInterval(checkInterval);
            }
        }, 500);
    }

    function clickTranscript() {
        const currentVideoId = getVideoId();

        // If ID changed or null, reset state
        if (currentVideoId !== lastVideoId) {
            attempts = 0;
            lastVideoId = currentVideoId;
        }

        if (!currentVideoId) return;

        // --- CHECK HISTORY ---
        if (hasAlreadyDownloaded(currentVideoId)) {
            log('Skipping ' + currentVideoId + ' (Already Done)');
            return;
        }

        if (attempts >= maxAttempts) {
            log('Max attempts reached for opening panel.');
            return;
        }

        if (isTranscriptOpen()) {
            waitForTranscriptAndDownload();
            return;
        }

        attempts++;

        const transcriptBtn = document.querySelector('button[aria-label="Show transcript"]');
        const secondaryBtn = document.querySelector('button[aria-label="Show transcript"]'); // sometimes selector varies

        if (transcriptBtn) {
            transcriptBtn.click();
            // Wait for panel to open and load
            setTimeout(() => {
                waitForTranscriptAndDownload();
            }, 1000);
            return;
        }

        // Retry
        setTimeout(clickTranscript, 800);
    }

    // --- EVENT LISTENERS ---

    // 1. Initial Load
    if (getVideoId()) {
        setTimeout(clickTranscript, 2000); // Wait for page hydration
    }

    // 2. Navigation (SPA behavior)
    window.addEventListener('yt-navigate-finish', () => {
        log('Navigation detected.');
        attempts = 0; // Reset attempts for new video
        setTimeout(clickTranscript, 1500);
    });

})();
