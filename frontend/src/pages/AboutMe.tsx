import type { ReactNode } from 'react';

import profilePhoto from '../assets/profolio.jpg';

export function AboutMe() {
  const profileLinks = [
    ['GitHub', 'https://github.com/callmeeric5'],
    ['LinkedIn', 'https://www.linkedin.com/in/callmeeric5/'],
  ];

  const personalInfo = [
    ['Name', 'Zihang Wang'],
    ['Location', 'Paris/France'],
    ['Focus', 'Machine learning, systems programming and algorithms'],
    ['Current work', 'MLE in distillation studio'],
  ];

  const workExperience = [
    {
      title: 'Full Stack Machine Learning Engineer',
      meta: 'Distillation Studio',
      body: 'AI integration and transition for small business.',
    },
    {
      title: 'Data Scientist',
      meta: 'Yso Corp',
      body: 'User install classification in RTB system',
    },
    {
      title: 'Data Scientist',
      meta: 'Trip.com',
      body: 'OCR and auto reconciliation of transaction receipts',
    },
  ];

  const education = [
    {
      title: '42 Paris',
      meta: 'Systems Programming',
      body: 'Project-based learning focused on C, Unix fundamentals, algorithms, debugging, collaboration, and building reliable programs from first principles.',
    },
    {
      title: 'EPITA',
      meta: 'Artificial Intelligence',
      body: ' ML and DL',
    },
    {
      title: 'Hong Kong Baptist University',
      meta: 'Computer Science',
      body: 'Foundation of computer science',
    },
  ];

  return (
    <div className="grid gap-8 rounded-2xl border border-[#e8e3d6] bg-[#fffdf8] p-6 lg:grid-cols-[0.72fr_1.28fr] lg:p-7">
      <aside className="rounded-2xl border border-[#e8e3d6] bg-[#f4f1e8] p-7">
        <div className="flex flex-col items-center text-center">
          <p className="text-sm font-semibold tracking-wide text-[#c96442]">About me</p>

          <h3 className="mt-3 font-serif text-4xl leading-tight text-[#171715]">Zihang Wang</h3>

          <img
            alt="Zihang Wang profile"
            className="mt-8 h-45 w-45 rounded-full border border-[#d8d1c2] object-cover shadow-sm sm:h-50 sm:w-50"
            src={profilePhoto}
          />

          <div className="mt-7 flex flex-row flex-wrap justify-center gap-3">
            {profileLinks.map(([label, href]) => (
              <a
                className="inline-flex min-h-10 items-center justify-center rounded-lg border border-[#e8e3d6] bg-[#fffdf8] px-5 text-sm font-semibold text-[#8a4429] transition hover:bg-[#faf9f5]"
                href={href}
                key={label}
                rel="noreferrer"
                target="_blank"
              >
                {label}
              </a>
            ))}
          </div>
        </div>

        <p className="mt-8 text-center text-base leading-8 text-[#5e5d59]">
          Building AI products by day.
          <br />
          Gaming and lifting after hours.
        </p>
      </aside>

      <div className="grid gap-7">
        <ResumeSection title="Personal info">
          <dl className="grid gap-3 sm:grid-cols-2">
            {personalInfo.map(([label, value]) => (
              <div className="rounded-xl border border-[#e8e3d6] bg-[#faf9f5] p-4" key={label}>
                <dt className="text-xs font-bold uppercase text-[#8b8174]">{label}</dt>
                <dd className="mt-1 text-sm font-semibold text-[#30302e]">{value}</dd>
              </div>
            ))}
          </dl>
        </ResumeSection>

        <ResumeSection title="Working experience">
          <div className="grid gap-4">
            {workExperience.map((item) => (
              <ResumeItem key={item.title} {...item} />
            ))}
          </div>
        </ResumeSection>

        <ResumeSection title="Educational experience">
          <div className="grid gap-4">
            {education.map((item) => (
              <ResumeItem key={item.title} {...item} />
            ))}
          </div>
        </ResumeSection>
      </div>
    </div>
  );
}

function ResumeSection({ children, title }: { children: ReactNode; title: string }) {
  return (
    <section>
      <h3 className="font-serif text-3xl leading-tight text-[#171715]">{title}</h3>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function ResumeItem({ body, meta, title }: { body: string; meta: string; title: string }) {
  return (
    <article className="border-t border-[#e8e3d6] pt-4">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
        <h4 className="text-lg font-semibold text-[#30302e]">{title}</h4>
        <p className="text-sm font-semibold text-[#8b8174]">{meta}</p>
      </div>
      <p className="mt-2 text-base leading-7 text-[#5e5d59]">{body}</p>
    </article>
  );
}
