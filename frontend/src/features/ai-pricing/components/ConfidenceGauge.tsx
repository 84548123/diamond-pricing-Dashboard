import React, { useEffect, useState } from 'react';

export const ConfidenceGauge: React.FC<{ score: number, size?: 'sm' | 'md' | 'lg' }> = ({ score, size = 'md' }) => {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    setTimeout(() => setAnimatedScore(score), 100);
  }, [score]);

  const sizes = { sm: 40, md: 64, lg: 96 };
  const strokeWidths = { sm: 4, md: 6, lg: 8 };
  
  const d = sizes[size];
  const strokeWidth = strokeWidths[size];
  const radius = (d - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDashoffset = circumference - (animatedScore / 100) * circumference;

  let strokeColor = 'url(#gauge-gradient-green)';
  if (score < 60) strokeColor = 'url(#gauge-gradient-red)';
  else if (score < 80) strokeColor = 'url(#gauge-gradient-yellow)';

  return (
    <div className="relative flex items-center justify-center" style={{ width: d, height: d }}>
      <svg className="transform -rotate-90 w-full h-full">
        <defs>
          <linearGradient id="gauge-gradient-green" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#34d399" />
            <stop offset="100%" stopColor="#10b981" />
          </linearGradient>
          <linearGradient id="gauge-gradient-yellow" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#fbbf24" />
            <stop offset="100%" stopColor="#f59e0b" />
          </linearGradient>
          <linearGradient id="gauge-gradient-red" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#fb7185" />
            <stop offset="100%" stopColor="#e11d48" />
          </linearGradient>
        </defs>
        <circle
          cx={d / 2}
          cy={d / 2}
          r={radius}
          stroke="rgba(255,255,255,0.1)"
          strokeWidth={strokeWidth}
          fill="none"
        />
        <circle
          cx={d / 2}
          cy={d / 2}
          r={radius}
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          style={{
            strokeDasharray: circumference,
            strokeDashoffset,
            transition: 'stroke-dashoffset 1s ease-out'
          }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`font-bold text-white ${size === 'sm' ? 'text-[10px]' : size === 'md' ? 'text-sm' : 'text-xl'}`}>
          {Math.round(animatedScore)}%
        </span>
      </div>
    </div>
  );
};
