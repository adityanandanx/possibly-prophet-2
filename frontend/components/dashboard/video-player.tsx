"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import {
  FiPlay,
  FiPause,
  FiVolume2,
  FiVolumeX,
  FiMaximize,
  FiMinimize,
  FiSkipBack,
  FiSkipForward,
} from "react-icons/fi";

interface VideoPlayerProps {
  src: string;
  title?: string;
  poster?: string;
}

export function VideoPlayer({ src, title, poster }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [showControls, setShowControls] = useState(true);
  const [volume, setVolume] = useState(1);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => setCurrentTime(video.currentTime);
    const handleLoadedMetadata = () => setDuration(video.duration);
    const handleEnded = () => setIsPlaying(false);

    video.addEventListener("timeupdate", handleTimeUpdate);
    video.addEventListener("loadedmetadata", handleLoadedMetadata);
    video.addEventListener("ended", handleEnded);

    return () => {
      video.removeEventListener("timeupdate", handleTimeUpdate);
      video.removeEventListener("loadedmetadata", handleLoadedMetadata);
      video.removeEventListener("ended", handleEnded);
    };
  }, []);

  useEffect(() => {
    let timeout: NodeJS.Timeout;
    if (isPlaying) {
      timeout = setTimeout(() => setShowControls(false), 3000);
    }
    return () => clearTimeout(timeout);
  }, [isPlaying, showControls]);

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const toggleFullscreen = () => {
    if (!containerRef.current) return;

    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const vol = parseFloat(e.target.value);
    if (videoRef.current) {
      videoRef.current.volume = vol;
      setVolume(vol);
      setIsMuted(vol === 0);
    }
  };

  const skip = (seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime += seconds;
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div
      ref={containerRef}
      className="video-player relative aspect-video bg-black rounded-3xl overflow-hidden group"
      onMouseMove={() => setShowControls(true)}
      onMouseLeave={() => isPlaying && setShowControls(false)}
    >
      <video
        ref={videoRef}
        src={src}
        poster={poster}
        className="w-full h-full object-contain"
        onClick={togglePlay}
      />

      {/* Play button overlay */}
      {!isPlaying && (
        <motion.div
          className="absolute inset-0 flex items-center justify-center bg-black/30"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.button
            className="w-20 h-20 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 flex items-center justify-center shadow-2xl"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={togglePlay}
          >
            <FiPlay className="w-8 h-8 text-white ml-1" />
          </motion.button>
        </motion.div>
      )}

      {/* Title bar */}
      {title && showControls && (
        <motion.div
          className="absolute top-0 left-0 right-0 p-4 bg-gradient-to-b from-black/70 to-transparent"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
        >
          <h3 className="text-white font-medium">{title}</h3>
        </motion.div>
      )}

      {/* Controls */}
      <motion.div
        className={`video-controls ${showControls ? "opacity-100" : "opacity-0"}`}
        initial={false}
        animate={{ opacity: showControls ? 1 : 0 }}
      >
        {/* Progress bar */}
        <div className="w-full mb-3">
          <input
            type="range"
            min={0}
            max={duration || 100}
            value={currentTime}
            onChange={handleSeek}
            className="w-full h-1 bg-white/30 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white"
            style={{
              background: `linear-gradient(to right, #3b82f6 0%, #6366f1 ${
                (currentTime / duration) * 100
              }%, rgba(255,255,255,0.3) ${(currentTime / duration) * 100}%, rgba(255,255,255,0.3) 100%)`,
            }}
          />
        </div>

        <div className="flex items-center gap-4">
          {/* Play/Pause */}
          <button
            onClick={togglePlay}
            className="p-2 hover:bg-white/20 rounded-full transition-colors"
          >
            {isPlaying ? (
              <FiPause className="w-5 h-5 text-white" />
            ) : (
              <FiPlay className="w-5 h-5 text-white" />
            )}
          </button>

          {/* Skip backward */}
          <button
            onClick={() => skip(-10)}
            className="p-2 hover:bg-white/20 rounded-full transition-colors"
          >
            <FiSkipBack className="w-4 h-4 text-white" />
          </button>

          {/* Skip forward */}
          <button
            onClick={() => skip(10)}
            className="p-2 hover:bg-white/20 rounded-full transition-colors"
          >
            <FiSkipForward className="w-4 h-4 text-white" />
          </button>

          {/* Time display */}
          <span className="text-white text-sm font-medium">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>

          <div className="flex-1" />

          {/* Volume */}
          <div className="flex items-center gap-2 group/volume">
            <button
              onClick={toggleMute}
              className="p-2 hover:bg-white/20 rounded-full transition-colors"
            >
              {isMuted || volume === 0 ? (
                <FiVolumeX className="w-5 h-5 text-white" />
              ) : (
                <FiVolume2 className="w-5 h-5 text-white" />
              )}
            </button>
            <input
              type="range"
              min={0}
              max={1}
              step={0.1}
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              className="w-0 group-hover/volume:w-20 transition-all duration-200 h-1 bg-white/30 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-2 [&::-webkit-slider-thumb]:h-2 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white"
            />
          </div>

          {/* Fullscreen */}
          <button
            onClick={toggleFullscreen}
            className="p-2 hover:bg-white/20 rounded-full transition-colors"
          >
            {isFullscreen ? (
              <FiMinimize className="w-5 h-5 text-white" />
            ) : (
              <FiMaximize className="w-5 h-5 text-white" />
            )}
          </button>
        </div>
      </motion.div>
    </div>
  );
}
