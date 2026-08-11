"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Video, MessageSquare, Users, Clock, Settings, BarChart2 } from "lucide-react"

export function Sidebar() {
  const pathname = usePathname()

  const navItems = [
    { name: "Dashboard", path: "/", icon: <BarChart2 className="h-4 w-4" /> },
    { name: "Channels", path: "/channel", icon: <Video className="h-4 w-4" /> },
    { name: "Research", path: "/research", icon: <MessageSquare className="h-4 w-4" /> },
    { name: "Audience", path: "/audience", icon: <Users className="h-4 w-4" /> },
    { name: "Timeline", path: "/timeline", icon: <Clock className="h-4 w-4" /> },
    { name: "Settings", path: "/settings", icon: <Settings className="h-4 w-4" /> },
  ]

  return (
    <div className="w-64 bg-background border-r flex flex-col">
      <div className="p-4 border-b">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <BarChart2 className="h-6 w-6" />
          YouTube Research
        </h1>
      </div>
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navItems.map((item) => (
            <li key={item.path}>
              <Link href={item.path} passHref>
                <Button
                  variant={pathname === item.path ? "secondary" : "ghost"}
                  className="w-full justify-start gap-2"
                >
                  {item.icon}
                  {item.name}
                </Button>
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  )
}