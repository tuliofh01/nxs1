interface FingerprintData {
  screen: string;
  colorDepth: number;
  timezone: string;
  platform: string;
  hardwareConcurrency: number;
  language: string;
}

async function fingerprint() {
  const data: FingerprintData = {
    screen: `${screen.width}x${screen.height}`,
    colorDepth: screen.colorDepth,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    platform: navigator.platform,
    hardwareConcurrency: navigator.hardwareConcurrency,
    language: navigator.language
  };

  try {
    await fetch("/api/fingerprint", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
  } catch (error) {
    console.error("Fingerprinting failed", error);
  }
}

fingerprint();
