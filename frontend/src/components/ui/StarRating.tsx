import React from 'react';
import { Star } from 'lucide-react';

export const StarRating: React.FC<{ rating: number, max?: number, className?: string }> = ({ rating, max = 5, className = '' }) => {
  return (
    <div className={`flex items-center space-x-1 ${className}`}>
      {[...Array(max)].map((_, i) => (
        <Star
          key={i}
          className={`w-4 h-4 ${i < rating ? 'fill-[url(#gold-gradient)] text-transparent' : 'fill-slate-700 text-slate-700'}`}
        />
      ))}
      <svg width="0" height="0" className="hidden">
        <defs>
          <linearGradient id="gold-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop stopColor="#fbbf24" offset="0%" />
            <stop stopColor="#f59e0b" offset="100%" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  );
};
