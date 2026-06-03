import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div style={{
      display: "flex",
      minHeight: "100vh",
      alignItems: "center",
      justifyContent: "center",
      background: "var(--background)",
    }}>
      <SignIn
        appearance={{
          elements: {
            rootBox: { width: "100%" , maxWidth: "420px" },
          },
        }}
      />
    </div>
  );
}
