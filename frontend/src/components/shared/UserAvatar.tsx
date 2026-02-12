import { Avatar, AvatarFallback } from "@/components/ui/avatar";

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((w) => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

// HSL-based colors generated from name hash — warm, saturated palette
// tuned for white text readability
const AVATAR_HUES = [174, 16, 262, 200, 340, 38, 152, 290, 120, 60];

function getAvatarColor(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = AVATAR_HUES[Math.abs(hash) % AVATAR_HUES.length];
  return `hsl(${hue}, 55%, 42%)`;
}

export function UserAvatar({
  name,
  size = "default",
}: {
  name: string;
  size?: "sm" | "default" | "lg";
}) {
  const sizeClass = {
    sm: "h-6 w-6 text-2xs",
    default: "h-8 w-8 text-xs",
    lg: "h-10 w-10 text-sm",
  }[size];

  const bgColor = getAvatarColor(name);

  return (
    <Avatar
      className={`${sizeClass} hover:scale-110 hover:shadow-md cursor-default`}
    >
      <AvatarFallback
        className="text-white font-heading font-semibold"
        style={{ backgroundColor: bgColor }}
      >
        {getInitials(name)}
      </AvatarFallback>
    </Avatar>
  );
}
