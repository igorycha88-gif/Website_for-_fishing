"use client";

interface MoonPhaseIconProps {
  phase: number | null;
  size?: number;
  className?: string;
}

export default function MoonPhaseIcon({
  phase,
  size = 24,
  className,
}: MoonPhaseIconProps) {
  const r = 10;
  const cx = 12;
  const cy = 12;

  if (phase === null || phase === undefined) {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        className={className}
      >
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="#94A3B8"
          stroke="#CBD5E1"
          strokeWidth={0.5}
        />
      </svg>
    );
  }

  const p = phase < 0 ? 0 : phase > 1 ? 1 : phase;
  const sweep = Math.cos(2 * Math.PI * p);
  const absSweep = Math.abs(sweep);
  const isWaxing = p <= 0.5;
  const isFullMoon = p >= 0.4375 && p <= 0.5625;
  const isNewMoon = p <= 0.0625 || p >= 0.9375;

  const darkSideSweepFlag = isWaxing ? 0 : 1;
  const terminatorSweepFlag = sweep >= 0 ? 1 : 0;
  const terminatorRx = absSweep * r;

  let shadowPath: string;
  if (isFullMoon) {
    shadowPath = "";
  } else if (isNewMoon) {
    shadowPath = `M ${cx} ${cy - r} A ${r} ${r} 0 1 1 ${cx} ${cy + r} A ${r} ${r} 0 1 1 ${cx} ${cy - r} Z`;
  } else {
    shadowPath = [
      `M ${cx} ${cy - r}`,
      `A ${r} ${r} 0 0 ${darkSideSweepFlag} ${cx} ${cy + r}`,
      `A ${terminatorRx} ${r} 0 0 ${terminatorSweepFlag} ${cx} ${cy - r}`,
      "Z",
    ].join(" ");
  }

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      className={className}
    >
      <circle cx={cx} cy={cy} r={r + 0.5} fill="#FDE68A" opacity={0.3} />
      <circle
        cx={cx}
        cy={cy}
        r={r}
        fill="#FCD34D"
        stroke="#F59E0B"
        strokeWidth={0.5}
      />
      {shadowPath && <path d={shadowPath} fill="#1E293B" />}
    </svg>
  );
}
