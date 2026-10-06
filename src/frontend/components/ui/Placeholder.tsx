import { ReactNode } from "react";

export default function Placeholder({
  icon,
  title,
  description,
}: {
  icon: ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 px-8 py-24 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-aura-purple-nav text-aura-purple [&>svg]:h-5 [&>svg]:w-5">
        {icon}
      </div>
      <p className="text-base font-semibold text-aura-navy">{title}</p>
      <p className="max-w-sm text-sm text-aura-gray">{description}</p>
    </div>
  );
}
