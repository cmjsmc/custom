import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "Comfy.BlobHistory",
    // Map<hash, { blobUrl: string, saveUrl: string }>
    processedBlobs: new Map(),

    async setup() {
        this.loadCSS();
        this.createPanel();

        document.addEventListener("ram-node-preview-generated", this.handlePreviewEvent.bind(this));

        console.log("Blob History panel setup complete.");
    },

    createPanel() {
        const panel = document.createElement("div");
        panel.id = "blob-history-panel";

        const header = document.createElement("div");
        header.id = "blob-history-header";
        header.innerHTML = `<h3>Blob History</h3>
            <div class="blob-history-controls">
                <button id="blob-history-clear" title="Clear History">Clear</button>
                <button id="blob-history-toggle" title="Toggle Panel">-</button>
            </div>`;

        const content = document.createElement("div");
        content.id = "blob-history-content";

        panel.appendChild(header);
        panel.appendChild(content);
        document.body.appendChild(panel);

        document.getElementById("blob-history-toggle").addEventListener("click", () => {
            const isHidden = content.style.display === "none";
            content.style.display = isHidden ? "flex" : "none";
            document.getElementById("blob-history-toggle").textContent = isHidden ? "-" : "+";
        });

        document.getElementById("blob-history-clear").addEventListener("click", () => {
            // Revoke all stored object URLs to release memory
            for (const [hash, { blobUrl, saveUrl }] of this.processedBlobs.entries()) {
                URL.revokeObjectURL(blobUrl);
                URL.revokeObjectURL(saveUrl);
            }
            this.processedBlobs.clear(); // Clear the tracking map

            content.innerHTML = ""; // Empty the visual panel

            // Dispatch an event to tell the private nodes to clear their previews
            document.dispatchEvent(new CustomEvent("ram-node-clear-previews"));
        });

        this.makeDraggable(panel, header);
    },

    loadCSS() {
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.type = "text/css";
        link.href = "extensions/private/blob_history.css";
        document.head.appendChild(link);
    },

    handlePreviewEvent(e) {
        if (e.detail?.url) {
            this.addBlobToHistory(e.detail.url);
        }
    },

    async addBlobToHistory(blobUrl) {
        try {
            const response = await fetch(blobUrl);
            const blobData = await response.blob();

            const buffer = await blobData.arrayBuffer();
            const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
            const hash = this.bufferToHex(hashBuffer);

            if (this.processedBlobs.has(hash)) {
                return; // Already in history, do nothing.
            }

            const mimeType = blobData.type;
            const extension = this.getExtensionForMimeType(mimeType);
            const filename = `blob_${hash.substring(0, 8)}${extension}`;

            // Create a separate URL for saving. This is good practice.
            const saveUrl = URL.createObjectURL(blobData);

            // Store both the display URL and the save URL for later revocation
            this.processedBlobs.set(hash, { blobUrl, saveUrl });

            this.createHistoryItem(blobUrl, saveUrl, hash, filename, mimeType);

        } catch (error) {
            console.error("Blob History Error:", error);
        }
    },

    createHistoryItem(displayUrl, saveUrl, hash, filename, mimeType) {
        const content = document.getElementById("blob-history-content");
        const item = document.createElement("div");
        item.className = "blob-history-item";
        item.dataset.hash = hash; // Store hash for removal

        let mediaElement;
        if (mimeType.startsWith("image/")) {
            mediaElement = document.createElement("img");
        } else if (mimeType.startsWith("video/")) {
            mediaElement = document.createElement("video");
            mediaElement.controls = true;
            mediaElement.autoplay = true;
            mediaElement.muted = true;
            mediaElement.loop = true;
        } else {
            return;
        }
        mediaElement.src = displayUrl;
        item.appendChild(mediaElement);

        const info = document.createElement("div");
        info.className = "info";
        info.innerHTML = `<span class="filename">${filename}</span>`;

        const removeButton = document.createElement("button");
        removeButton.textContent = "Remove";
        removeButton.className = "remove-button";
        removeButton.onclick = () => {
            const itemData = this.processedBlobs.get(hash);
            if (itemData) {
                URL.revokeObjectURL(itemData.blobUrl);
                URL.revokeObjectURL(itemData.saveUrl);
                this.processedBlobs.delete(hash);
            }
            item.remove();
        };

        const saveButton = document.createElement("a");
        saveButton.className = "save-button";
        saveButton.href = saveUrl;
        saveButton.textContent = "Save";
        saveButton.setAttribute("download", filename);

        const buttonContainer = document.createElement("div");
        buttonContainer.append(saveButton, removeButton);
        info.appendChild(buttonContainer);

        item.appendChild(info);
        content.prepend(item);
    },

    bufferToHex(buffer) {
        return [...new Uint8Array(buffer)]
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    },

    getExtensionForMimeType(mimeType) {
        const mimeMap = {
            'image/png': '.png', 'image/jpeg': '.jpg', 'image/gif': '.gif',
            'image/webp': '.webp', 'video/mp4': '.mp4', 'video/webm': '.webm',
        };
        return mimeMap[mimeType] || '.bin';
    },

    makeDraggable(panel, handle) {
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        handle.onmousedown = (e) => {
            if (e.target.tagName === 'BUTTON') return; // Don't drag when clicking buttons
            e.preventDefault();
            pos3 = e.clientX;
            pos4 = e.clientY;
            document.onmouseup = () => { document.onmouseup = null; document.onmousemove = null; };
            document.onmousemove = (e) => {
                e.preventDefault();
                pos1 = pos3 - e.clientX;
                pos2 = pos4 - e.clientY;
                pos3 = e.clientX;
                pos4 = e.clientY;
                panel.style.top = (panel.offsetTop - pos2) + "px";
                panel.style.left = (panel.offsetLeft - pos1) + "px";
            };
        };
    }
});