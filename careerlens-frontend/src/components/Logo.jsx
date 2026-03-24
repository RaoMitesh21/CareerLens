/* ═══════════════════════════════════════════════════════════════════
   Logo — CareerLens FINAL brand mark (inline SVG)
   ═══════════════════════════════════════════════════════════════════
   Icon: Two concentric C-arcs (gunmetal) + zigzag trend arrow (cyan)
   Text: "Career" in gunmetal, "Lens" in cyan — Arial 800
   THIS IS THE ONLY LOGO. Used everywhere.
   ═══════════════════════════════════════════════════════════════════ */

const GUNMETAL = '#232B32';
const CYAN = '#00C2CB';

/**
 * Icon-only mark — the C-rings + trend arrow, no text.
 * Used in loading overlays, avatar fallbacks, empty states.
 * @param {{ size?: number }} props
 */
export function LogoIcon({ size = 32 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="-55 -55 110 110"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Outer C arc */}
      <path
        d="M 35,-35 A 50,50 0 1,0 35,35"
        stroke={GUNMETAL}
        strokeWidth="14"
        strokeLinecap="round"
        fill="none"
      />
      {/* Inner C arc */}
      <path
        d="M 20,-20 A 28,28 0 1,0 20,20"
        stroke={GUNMETAL}
        strokeWidth="14"
        strokeLinecap="round"
        fill="none"
      />
      {/* White mask behind arrow */}
      <polyline
        points="-30,30 0,0 15,10 55,-35"
        stroke="#FFFFFF"
        strokeWidth="22"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      {/* Cyan trend arrow */}
      <polyline
        points="-30,30 0,0 15,10 55,-35"
        stroke={CYAN}
        strokeWidth="10"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      {/* Arrow head */}
      <path
        d="M 35,-35 L 55,-35 L 55,-15"
        stroke={CYAN}
        strokeWidth="10"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  );
}

/**
 * Full logo — icon + "CareerLens" wordmark
 * @param {{ size?: 'sm' | 'md' | 'lg' }} props
 */
export default function Logo({ size = 'md' }) {
  const heights = { sm: 28, md: 38, lg: 56 };
  const h = heights[size];
  // Original viewBox is 600×150 — aspect ratio 4:1
  const w = h * 4;

  return (
    <svg
      width={w}
      height={h}
      viewBox="0 0 600 150"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ display: 'block' }}
    >
      {/* ── Icon group ──────────────────────────────────────────── */}
      <g transform="translate(80, 75)">
        {/* Outer C arc */}
        <path
          d="M 35,-35 A 50,50 0 1,0 35,35"
          stroke={GUNMETAL}
          strokeWidth="14"
          strokeLinecap="round"
          fill="none"
        />
        {/* Inner C arc */}
        <path
          d="M 20,-20 A 28,28 0 1,0 20,20"
          stroke={GUNMETAL}
          strokeWidth="14"
          strokeLinecap="round"
          fill="none"
        />
        {/* White mask behind arrow */}
        <polyline
          points="-30,30 0,0 15,10 55,-35"
          stroke="#FFFFFF"
          strokeWidth="22"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
        {/* Cyan trend arrow */}
        <polyline
          points="-30,30 0,0 15,10 55,-35"
          stroke={CYAN}
          strokeWidth="10"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
        {/* Arrow head */}
        <path
          d="M 35,-35 L 55,-35 L 55,-15"
          stroke={CYAN}
          strokeWidth="10"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
      </g>

      {/* ── Wordmark ────────────────────────────────────────────── */}
      <g transform="translate(160, 95)">
        <text
          fontFamily="Arial, Helvetica, sans-serif"
          fontWeight="800"
          fontSize="68"
          letterSpacing="-1"
        >
          <tspan fill={GUNMETAL}>Career</tspan>
          <tspan fill={CYAN}>Lens</tspan>
        </text>
      </g>
    </svg>
  );
}
