"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bot, FileText, Layers3, Search } from "lucide-react";

const items = [
  { href: "/chat", label: "Chat", icon: Bot },
  { href: "/search", label: "Search", icon: Search },
  { href: "/sow", label: "SOW", icon: FileText },
  { href: "/resources", label: "Resources", icon: Layers3 },
];

export default function AppNav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-20 border-b border-white/10 bg-zinc-950/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
        <div>
          <p className="text-m font-semibold uppercase tracking-[0.3em] text-[#c90c61]">
            Enterprise Discovery-to-Delivery
          </p>
        </div>

        <nav className="flex flex-wrap gap-2 rounded-full border border-white/10 bg-white/5 p-1.5">
          {items.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium transition ${
                  isActive
                    ? "bg-white text-zinc-950 shadow-lg"
                    : "text-zinc-300 hover:bg-zinc-800 hover:text-white"
                }`}
              >
                <Icon size={16} />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
