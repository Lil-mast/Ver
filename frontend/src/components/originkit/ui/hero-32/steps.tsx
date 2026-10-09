"use client";

const SHEEN_FILL = "linear-gradient(0deg, #afafaf 0%, #d7d7d7 100%)";
const SHEEN = "bg-clip-text text-transparent";

const STEPS = [
  {
    number: "01",
    title: "Connect",
    body: "Integrate your data, APIs, and existing tools in minutes with secure infrastructure.",
  },
  {
    number: "02",
    title: "Automate",
    body: "Build intelligent workflows powered by AI agents that reason, execute, and adapt.",
  },
  {
    number: "03",
    title: "Scale",
    body: "Deploy globally with enterprise-grade reliability, monitoring, and continuous optimization.",
  },
];

export const Steps = () => (
  <section
    aria-labelledby="hero-32-steps"
    className="shrink-0 px-[25px] pt-[23px] pb-[40px] ipad:px-[48px] ipad:pt-[27px] ipad:pb-[39px] desktop-sm:px-[41px] desktop-sm:pt-[32px] desktop-sm:pb-[49px]"
  >
    <h2
      id="hero-32-steps"
      style={{ backgroundImage: SHEEN_FILL }}
      className={`font-gemunu text-[20px] leading-[25px] font-medium capitalize ipad:text-[32px] ipad:leading-[40px] ${SHEEN}`}
    >
      From Idea to Production in Three Steps :
    </h2>

    <ol className="mt-[12px] grid grid-cols-1 md:grid-cols-3 gap-[26px] ipad:mt-[25px] ipad:gap-[45px] desktop-sm:mt-[24px] desktop-sm:gap-[60px]">
      {STEPS.map(({ number, title, body }) => (
        <li key={number}>
          {}
          <span
            aria-hidden
            className="flex size-[21px] items-center justify-center bg-[#d8d8d8] shadow-[inset_0px_0px_2.4px_0px_rgba(249,109,9,0.1)] ipad:size-[34px] ipad:shadow-[inset_0px_0px_3.9px_0px_rgba(249,109,9,0.1)] desktop-sm:size-[44px] desktop-sm:shadow-[inset_0px_0px_5px_0px_rgba(249,109,9,0.1)]"
          >
            <span className="font-geist text-[9.7px] leading-[10px] font-semibold text-[#242424] ipad:text-[15.5px] ipad:leading-[16px] desktop-sm:text-[20px] desktop-sm:leading-[21px]">
              {number}
            </span>
          </span>

          <h3
            style={{ backgroundImage: SHEEN_FILL }}
            className={`mt-[8px] font-geist text-[13px] leading-[13.75px] font-medium capitalize ipad:mt-[13px] ipad:text-[18px] ipad:leading-[22px] desktop-sm:mt-[16px] desktop-sm:text-[20px] desktop-sm:leading-[21px] ${SHEEN}`}
          >
            {title}
          </h3>

          <p className="mt-[6px] max-w-[300px] iphone:max-w-none text-balance font-geist leading-5 font-medium text-[#707070] capitalize ipad:mt-[12px] text-[13px] ipad:leading-[16px] desktop-sm:mt-[16px] desktop-sm:text-[15px] desktop-sm:leading-[21px]">
            {body}
          </p>
        </li>
      ))}
    </ol>
  </section>
);