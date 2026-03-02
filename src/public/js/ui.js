async function fingerprint() {
  const data = {
    screen: `${screen.width}x${screen.height}`,
    colorDepth: screen.colorDepth,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    platform: navigator.platform,
    hardwareConcurrency: navigator.hardwareConcurrency,
    language: navigator.language
  };

  await fetch("/api/fingerprint", {
    method: "POST",
    body: JSON.stringify(data)
  });
}

fingerprint();
