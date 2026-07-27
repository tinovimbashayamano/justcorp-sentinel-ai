export function base64ToBlob(base64, mediaType) {
  const binary = window.atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (
    let index = 0;
    index < binary.length;
    index += 1
  ) {
    bytes[index] = binary.charCodeAt(index);
  }
  return new Blob([bytes], { type: mediaType });
}

export function createDataUrl(
  base64,
  mediaType = "image/png",
) {
  return `data:${mediaType};base64,${base64}`;
}

export function downloadBase64File({
  base64,
  mediaType,
  filename,
}) {
  const objectUrl = URL.createObjectURL(
    base64ToBlob(base64, mediaType),
  );
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}
