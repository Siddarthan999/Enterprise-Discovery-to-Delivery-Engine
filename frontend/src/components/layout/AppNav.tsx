"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bot, CircleCheck , FileText, Layers3, Search } from "lucide-react";
import Image from "next/image";
import App from "next/app";

const items = [
  { href: "/chat", label: "Chat", icon: Bot },
  { href: "/search", label: "Search", icon: Search },
  { href: "/sow", label: "SOW", icon: FileText },
  { href: "/resources", label: "Resources", icon: Layers3 },
  { href: "/approval", label: "Approval", icon: CircleCheck },
];

export default function AppNav() {
  const pathname = usePathname();

  return (
      <header className="sticky top-0 z-20 border-b border-white/10 bg-zinc-950/80 backdrop-blur-xl">
        <div className="flex flex-wrap items-center justify-between gap-4 px-5 py-4 sm:px-8 lg:px-10">
          <div className="flex shrink-0 items-center gap-5">
            {/* Logo */}
            <div className="rounded-xl bg-white p-2 shadow-lg shadow-black/20">
              <Image
                src="/logo-cprime.svg"
                alt="Cprime Logo"
                width={38}
                height={38}
                className="h-8 w-auto"
              />
            </div>

            {/* Divider */}
            <div className="h-10 w-px bg-white/10" />

            {/* Product Branding */}
            <div className="flex flex-col leading-tight">
              <span className="text-[10px] uppercase tracking-[0.35em] text-zinc-500">
                Enterprise Platform
              </span>

              <span className="text-sm font-semibold uppercase tracking-[0.22em] text-[#c90c61]">
                Discovery-to-Delivery
              </span>
            </div>
          </div>

        <nav className="flex flex-wrap justify-end gap-2 rounded-full border border-white/10 bg-white/5 p-1.5">
          {items.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`shrink-0 flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium transition ${
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
