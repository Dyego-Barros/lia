type ContactAvatarProps = {
  photoUrl?: string | null;
  size?: "small" | "medium" | "large";
};

const sizes = {
  small: "h-9 w-9",
  medium: "h-10 w-10",
  large: "h-11 w-11",
};

export function ContactAvatar({ photoUrl, size = "medium" }: ContactAvatarProps) {
  const normalizedPhotoUrl = photoUrl?.replaceAll("&amp;", "&").replaceAll("&quot;", '"').replace(/^['"]|['"]$/g, "");
  return normalizedPhotoUrl ? (
    <span
      aria-label="Foto do contato"
      className={`relative flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-fuchsia-50 text-fuchsia-700 ${sizes[size]}`}
    >
      <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={`absolute ${size === "large" ? "h-5 w-5" : "h-[18px] w-[18px]"}`}>
        <circle cx="12" cy="8" r="3" />
        <path d="M5.5 20a6.5 6.5 0 0 1 13 0" />
      </svg>
      <img
        src={normalizedPhotoUrl}
        alt="Foto do contato"
        referrerPolicy="no-referrer"
        className="relative z-10 h-full w-full object-cover"
        onError={(event) => { event.currentTarget.style.display = "none"; }}
      />
    </span>
  ) : (
    <span className={`flex shrink-0 items-center justify-center rounded-full bg-fuchsia-50 text-fuchsia-700 ${sizes[size]}`}>
      <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={size === "large" ? "h-5 w-5" : "h-[18px] w-[18px]"}>
        <circle cx="12" cy="8" r="3" />
        <path d="M5.5 20a6.5 6.5 0 0 1 13 0" />
      </svg>
    </span>
  );
}
