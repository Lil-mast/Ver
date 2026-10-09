"use client";

function asset(file: string) {
  return `/originkit/hero-32/${file}`;
}

const NAV_LINKS = ["Protocol", "Developers", "Integrations", "Community"];

const CONTROL =
  "cursor-pointer touch-manipulation [-webkit-tap-highlight-color:transparent] transition-[opacity,transform] duration-200 ease-out focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white active:scale-[0.97] motion-reduce:active:scale-100 [@media(hover:hover)_and_(pointer:fine)]:hover:opacity-70";

const LINK =
  "font-geist text-[15px] leading-[21px] font-medium uppercase text-white/65";

export const Navbar = () => (
  <nav
    aria-label="Primary"

    className="relative flex h-[70px] shrink-0 items-center border-b border-solid border-white/16 px-[5px] ipad:h-[62px] ipad:px-[48px] desktop-sm:h-[94px] desktop-sm:px-[40px]"
  >
    <a
      href="#"
      aria-label="Deblot home"
      className={`font-gemunu text-[32px] leading-[24px] font-semibold tracking-[-0.02em] text-white ${CONTROL}`}
    >
      DEBLOT
    </a>

    <ul className="absolute top-1/2 left-1/2 hidden -translate-x-1/2 -translate-y-1/2 items-center gap-[33px] desktop-sm:flex">
      {NAV_LINKS.map((label) => (
        <li key={label}>
          <a
            href="#"
            className={`flex min-h-11 items-center whitespace-nowrap ${LINK} ${CONTROL}`}
          >
            / {label}
          </a>
        </li>
      ))}
    </ul>

    {}
    <button
      type="button"
      aria-label="Open menu"
      className={`relative ml-auto size-6 shrink-0 ipad:size-8 desktop-sm:hidden ${CONTROL}`}
    >
      <span aria-hidden className="absolute -inset-2.5" />
      <img
        src={asset("menu.svg")}
        alt=""
        aria-hidden
        className="relative block size-full max-w-none"
      />
    </button>

    <button
      type="button"
      className={`ml-auto hidden h-[49px] w-[117px] shrink-0 items-center justify-center border border-solid border-[#d9d9d9] font-geist text-[15px] leading-[21px] font-medium uppercase text-white desktop-sm:inline-flex ${CONTROL}`}
    >
      Contact
    </button>
  </nav>
);