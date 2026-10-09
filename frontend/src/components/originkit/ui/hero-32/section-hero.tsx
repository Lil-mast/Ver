"use client";

"use client";

import { AsciiPortrait } from "@/components/originkit/ui/hero-32/ascii-portrait";
import { Navbar } from "@/components/originkit/ui/hero-32/navbar";
import { Steps } from "@/components/originkit/ui/hero-32/steps";

const PAGE = "bg-[#232323]";

const RULE = "border-solid border-white/16";

export const SectionHero = () => (
  <main
    className={`animate-hero-reveal relative flex min-h-dvh w-full flex-col ${PAGE}`}
  >
    <div className="mx-auto flex w-full max-w-[1440px] flex-1 flex-col min-h-[874px] ipad:min-h-[1068px] desktop-sm:min-h-[831px]">
      <div
        className={`mx-[11px] flex flex-1 flex-col border-x ${RULE} ipad:mx-[62px] desktop-sm:mx-[80px]`}
      >
        {}
        <div className="contents desktop-sm:flex desktop-sm:max-h-[1141px] desktop-sm:flex-1 desktop-sm:flex-col">
          <Navbar />

          {}
          <div
            className={`flex h-[605px] shrink-0 flex-col border-b ${RULE} ipad:h-[746px] desktop-sm:h-[453px] desktop-sm:grow desktop-sm:flex-row`}
          >
            {}
            <div
              className={`flex flex-1 justify-center overflow-hidden border-b ${RULE} desktop-sm:w-[510px] desktop-sm:flex-none desktop-sm:border-b-0`}
            >
              {}
              <div className="relative aspect-[1024/1536] h-[130%] w-auto shrink-0">
                <AsciiPortrait />
              </div>
            </div>

            {}
            <div className="flex min-h-[263px] shrink-0 flex-col justify-start px-[25px] pt-[21px] ipad:min-h-[340px] ipad:px-[48px] ipad:pt-[38px] desktop-sm:min-h-0 desktop-sm:flex-1 desktop-sm:justify-center desktop-sm:pt-[41px] desktop-sm:pr-[16px] desktop-sm:pl-[49px]">
              {}
              <p className="relative flex h-[36px] w-[216px] shrink-0 items-center justify-center bg-white/10 font-geist text-[16px] leading-[24px] tracking-[0.02em] text-[#fffbf9] capitalize">
                AI Infrastructure Platform
                <span
                  aria-hidden
                  className="pointer-events-none absolute -top-px -left-px size-[4px] border-t border-l border-solid border-white/50"
                />
                <span
                  aria-hidden
                  className="pointer-events-none absolute -top-px -right-px size-[4px] border-t border-r border-solid border-white/50"
                />
                <span
                  aria-hidden
                  className="pointer-events-none absolute -bottom-px -left-px size-[4px] border-b border-l border-solid border-white/50"
                />
                <span
                  aria-hidden
                  className="pointer-events-none absolute -right-px -bottom-px size-[4px] border-r border-b border-solid border-white/50"
                />
              </p>

              {}
              <h1 className="mt-[17px] font-gemunu text-[38px] leading-[43.3px] font-medium tracking-[-0.02em] text-white ipad:mt-[13px] ipad:text-[68px] ipad:leading-[72px] max-w-[705px]">
                Build, Deploy &amp; Scale Intelligent Systems
              </h1>

              {}
              <div className="mt-[20px] flex flex-wrap items-center gap-[16px] ipad:mt-[28px] desktop-sm:mt-[23px]">
                <button
                  type="button"
                  className="inline-flex h-[48px] w-[125px] shrink-0 cursor-pointer items-center justify-center border border-solid border-[#dbdbdb] font-geist text-[15px] leading-[21px] font-medium text-white capitalize transition-[opacity,transform] duration-200 ease-out [-webkit-tap-highlight-color:transparent] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white active:scale-[0.97] motion-reduce:active:scale-100 [@media(hover:hover)_and_(pointer:fine)]:hover:opacity-70"
                >
                  Get started
                </button>
                <button
                  type="button"
                  className="relative inline-flex h-[48px] w-[145px] shrink-0 cursor-pointer items-center justify-center bg-[#d9d9d9] font-geist text-[15px] leading-[21px] font-medium text-[#252525] capitalize shadow-[inset_0px_0px_5px_0px_rgba(249,109,9,0.1)] transition-[opacity,transform] duration-200 ease-out [-webkit-tap-highlight-color:transparent] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white active:scale-[0.97] motion-reduce:active:scale-100 [@media(hover:hover)_and_(pointer:fine)]:hover:opacity-90"
                >
                  Launch demo
                </button>
              </div>
            </div>
          </div>

          <Steps />
        </div>
      </div>
    </div>
  </main>
);