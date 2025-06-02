const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

const noteInput = document.getElementById('noteInput');
const notesDisplay = document.getElementById('notesDisplay');
const fileUpload = document.getElementById('fileUpload');
const uploadBtn = document.querySelector('.upload-btn');
const uploadMode = document.getElementById('uploadMode');
const modal = document.getElementById('imageModal');
const modalImage = document.getElementById('modalImage');
const closeBtn = document.querySelector('.close-btn');
const CHUNK_SIZE = 1 * 1024 * 1024; // 1MB 分片大小

let scale = 1;
const minScale = 0.1;
const maxScale = 3;
const scaleStep = 0.1;
let isDragging = false;
let startX, startY, initialX = 0, initialY = 0;
let pinchStartDistance = 0;
let currentEditingNote = null;

// 仅在 notes.html 页面中执行相关逻辑
if (notesDisplay && noteInput) {
    // --- 打开模态框 ---
    notesDisplay.addEventListener('click', (event) => {
        if (event.target.tagName === 'IMG' && event.target.dataset.fullSrc) {
            modal.style.display = 'flex';
            modalImage.src = event.target.dataset.fullSrc;
            scale = 1;
            initialX = 0;
            initialY = 0;
            modalImage.style.transform = `scale(${scale}) translate(${initialX}px, ${initialY}px)`;
        }
    });

    // --- 关闭模态框 ---
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
            modalImage.src = '';
            modalImage.style.transform = 'scale(1) translate(0px, 0px)';
            scale = 1;
            initialX = 0;
            initialY = 0;
        });
    }

    // --- 点击模态框外部关闭 ---
    if (modal) {
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                modal.style.display = 'none';
                modalImage.src = '';
                modalImage.style.transform = 'scale(1) translate(0px, 0px)';
                scale = 1;
                initialX = 0;
                initialY = 0;
            }
        });
    }

    // --- ESC 键处理 ---
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && modal && modal.style.display === 'flex') {
            if (scale !== 1 || initialX !== 0 || initialY !== 0) {
                scale = 1;
                initialX = 0;
                initialY = 0;
                modalImage.style.transform = `scale(${scale}) translate(${initialX}px, ${initialY}px)`;
            } else {
                modal.style.display = 'none';
                modalImage.src = '';
                modalImage.style.transform = 'scale(1) translate(0px, 0px)';
            }
        }
    });

    // --- 页面加载时确保模态框不显示并初始化画廊 ---
    document.addEventListener('DOMContentLoaded', () => {
        if (modal) modal.style.display = 'none';

        // 初始化笔记内容中的链接
        document.querySelectorAll('.note-text').forEach(p => {
            p.innerHTML = convertUrlsToLinks(p.dataset.rawText);
        });

        // 初始隐藏保存和取消按钮
        document.querySelectorAll('.note-actions .btn-save, .note-actions .btn-cancel').forEach(btn => {
            btn.style.display = 'none';
        });

        // 初始化画廊
        initializeGalleries();
    });

    // --- 鼠标滚轮缩放 ---
    if (modalImage) {
        modalImage.addEventListener('wheel', (event) => {
            event.preventDefault();
            const rect = modalImage.getBoundingClientRect();
            const mouseX = event.clientX - rect.left;
            const mouseY = event.clientY - rect.top;
            const delta = event.deltaY > 0 ? -scaleStep : scaleStep;
            const newScale = Math.min(maxScale, Math.max(minScale, scale + delta));
            if (newScale === scale) return;
            const offsetX = (mouseX - rect.width / 2) / scale;
            const offsetY = (mouseY - rect.height / 2) / scale;
            const scaleRatio = newScale / scale;
            initialX = initialX * scaleRatio - offsetX * (newScale - scale);
            initialY = initialY * scaleRatio - offsetY * (newScale - scale);
            scale = newScale;
            modalImage.style.transform = `scale(${scale}) translate(${initialX}px, ${initialY}px)`;
        });

        // --- 图片拖拽 ---
        modalImage.addEventListener('mousedown', (event) => {
            if (scale <= 1) return;
            isDragging = true;
            startX = event.clientX;
            startY = event.clientY;
            const transform = modalImage.style.transform.match(/translate\(([^)]+)\)/);
            if (transform) {
                const [x, y] = transform[1].split(',').map(val => parseFloat(val));
                initialX = x || 0;
                initialY = y || 0;
            }
            modalImage.style.cursor = 'grabbing';
        });

        modalImage.addEventListener('mousemove', (event) => {
            if (!isDragging) return;
            event.preventDefault();
            const dx = event.clientX - startX;
            const dy = event.clientY - startY;
            modalImage.style.transform = `scale(${scale}) translate(${initialX + dx}px, ${initialY + dy}px)`;
        });

        modalImage.addEventListener('mouseup', () => {
            isDragging = false;
            const transform = modalImage.style.transform.match(/translate\(([^)]+)\)/);
            if (transform) {
                const [x, y] = transform[1].split(',').map(val => parseFloat(val));
                initialX = x || 0;
                initialY = y || 0;
            }
            modalImage.style.cursor = 'grab';
        });

        modalImage.addEventListener('mouseleave', () => {
            isDragging = false;
            modalImage.style.cursor = 'grab';
        });

        // --- 手机端双指缩放和拖拽 ---
        modalImage.addEventListener('touchstart', (event) => {
            if (event.touches.length === 2) {
                event.preventDefault();
                const touch1 = event.touches[0];
                const touch2 = event.touches[1];
                pinchStartDistance = Math.hypot(touch1.pageX - touch2.pageX, touch1.pageY - touch2.pageY);
            } else if (event.touches.length === 1 && scale > 1) {
                isDragging = true;
                startX = event.touches[0].clientX;
                startY = event.touches[0].clientY;
                const transform = modalImage.style.transform.match(/translate\(([^)]+)\)/);
                if (transform) {
                    const [x, y] = transform[1].split(',').map(val => parseFloat(val));
                    initialX = x || 0;
                    initialY = y || 0;
                }
            }
        });

        modalImage.addEventListener('touchmove', (event) => {
            if (event.touches.length === 2) {
                event.preventDefault();
                const touch1 = event.touches[0];
                const touch2 = event.touches[1];
                const currentDistance = Math.hypot(touch1.pageX - touch2.pageX, touch1.pageY - touch2.pageY);
                const newScale = scale * (currentDistance / pinchStartDistance);
                if (newScale >= minScale && newScale <= maxScale) {
                    scale = newScale;
                    modalImage.style.transform = `scale(${scale}) translate(${initialX}px, ${initialY}px)`;
                }
                pinchStartDistance = currentDistance;
            } else if (event.touches.length === 1 && isDragging) {
                event.preventDefault();
                const dx = event.touches[0].clientX - startX;
                const dy = event.touches[0].clientY - startY;
                modalImage.style.transform = `scale(${scale}) translate(${initialX + dx}px, ${initialY + dy}px)`;
            }
        });

        modalImage.addEventListener('touchend', () => {
            isDragging = false;
            pinchStartDistance = 0;
            const transform = modalImage.style.transform.match(/translate\(([^)]+)\)/);
            if (transform) {
                const [x, y] = transform[1].split(',').map(val => parseFloat(val));
                initialX = x || 0;
                initialY = y || 0;
            }
        });
    }

    // --- 文件上传逻辑 ---
    if (uploadBtn && fileUpload) {
        uploadBtn.addEventListener('click', () => {
            fileUpload.click();
        });

        fileUpload.addEventListener('change', (event) => {
            const files = Array.from(event.target.files);
            if (files.length === 0) return;

            const mode = uploadMode ? uploadMode.value : 'single';
            if (mode === 'single') {
                if (files.length > 1) {
                    alert('单张上传模式下只能选择一张图片！');
                    fileUpload.value = '';
                    return;
                }
                console.log('File selected:', files[0].name);
                uploadFileInChunks(files[0]);
            } else if (mode === 'gallery' || mode === 'zip') {
                if (files.length > 30) {
                    alert('一次最多上传 30 张图片！');
                    fileUpload.value = '';
                    return;
                }
                uploadMultipleFiles(files, mode);
            }
            fileUpload.value = '';
        });
    }

    // --- 粘贴处理 ---
    noteInput.addEventListener('paste', (event) => {
        console.log('Paste event triggered');
        const items = (event.clipboardData || window.clipboardData).items;
        let pastedText = event.clipboardData.getData('text/plain');
        let foundImage = false;
        for (let i = 0; i < items.length; i++) {
            if (items[i].type.indexOf('image') !== -1) {
                const blob = items[i].getAsFile();
                if (!blob) continue;
                foundImage = true;
                event.preventDefault();
                const reader = new FileReader();
                reader.onload = function(loadEvent) {
                    const tempFileName = `pasted-image-${Date.now()}.png`;
                    sendNoteData('image', loadEvent.target.result, tempFileName);
                };
                reader.readAsDataURL(blob);
                if (pastedText.trim()) {
                    sendNoteData('text', pastedText.trim());
                    pastedText = '';
                }
                break;
            }
        }
        if (!foundImage && pastedText.trim()) {
            event.preventDefault();
            sendNoteData('text', pastedText.trim());
        }
    });

    // --- 文本提交 ---
    noteInput.addEventListener('keydown', (event) => {
        console.log('Keydown event:', event.key);
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            const textContent = noteInput.innerText.trim();
            console.log('Enter pressed, text:', textContent);
            if (textContent) {
                sendNoteData('text', textContent);
                noteInput.innerText = '';
            }
        }
    });
}

// --- 初始化画廊 ---
function initializeGalleries() {
    const galleries = document.querySelectorAll('.gallery-container');
    if (!galleries.length) return;

    galleries.forEach(container => {
        const gallery = container.querySelector('.gallery');
        if (!gallery) return;

        let images = [];
        try {
            const imagesStr = container.getAttribute('data-images') || '[]';
            console.log('Parsing data-images:', imagesStr); // 调试信息
            if (imagesStr && imagesStr.trim() !== '') {
                images = JSON.parse(imagesStr);
            } else {
                images = [];
            }
        } catch (e) {
            console.error('Error parsing gallery images:', e);
            images = [];
        }
        if (!Array.isArray(images)) {
            images = [images];
        }
        container.setAttribute('data-images', JSON.stringify(images));
        const leftArrow = container.querySelector('.arrow-left');
        const rightArrow = container.querySelector('.arrow-right');
        let currentPage = parseInt(container.dataset.currentPage || '0', 10);
        const imagesPerPage = 3;
        const totalPages = Math.ceil(images.length / imagesPerPage);

        const updateGallery = () => {
            console.log('Updating gallery, currentPage:', currentPage, 'images:', images); // 调试信息
            const start = currentPage * imagesPerPage;
            const end = Math.min(start + imagesPerPage, images.length);
            const allImages = gallery.querySelectorAll('img');
            allImages.forEach((img, index) => {
                if (index >= start && index < end) {
                    img.style.display = 'block';
                } else {
                    img.style.display = 'none';
                }
            });
            if (leftArrow) leftArrow.style.display = currentPage === 0 ? 'none' : 'block';
            if (rightArrow) rightArrow.style.display = currentPage === totalPages - 1 || images.length === 0 ? 'none' : 'block';
            container.dataset.currentPage = currentPage;
        };

        updateGallery();

        // 触摸滑动
        let touchStartX = 0;
        gallery.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
        });

        gallery.addEventListener('touchend', (e) => {
            const touchEndX = e.changedTouches[0].clientX;
            const swipeDistance = touchEndX - touchStartX;
            if (swipeDistance > 50 && currentPage > 0) {
                currentPage--;
                updateGallery();
            } else if (swipeDistance < -50 && currentPage < totalPages - 1) {
                currentPage++;
                updateGallery();
            }
        });

        // 箭头点击事件
        container.addEventListener('click', (event) => {
            const arrow = event.target.closest('.gallery-arrow');
            if (!arrow) return;
            if (arrow.classList.contains('arrow-left')) {
                if (currentPage > 0) currentPage--;
            } else if (arrow.classList.contains('arrow-right')) {
                if (currentPage < totalPages - 1) currentPage++;
            }
            updateGallery();
        });
    });
}

// --- 上传单个文件 ---
async function uploadFileInChunks(file) {
    const chunkSize = CHUNK_SIZE;
    const totalChunks = Math.ceil(file.size / chunkSize);
    const chunkId = `chunk-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const filename = file.name.toLowerCase();
    console.log(`File selected: ${filename}`);
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressContainer = document.getElementById('uploadProgress');
    if (!progressBar || !progressText || !progressContainer) return;

    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';
    progressText.textContent = '0%';

    for (let i = 0; i < totalChunks; i++) {
        const start = i * chunkSize;
        const end = Math.min(start + chunkSize, file.size);
        const chunk = file.slice(start, end);
        const formData = new FormData();
        formData.append('chunk', chunk, filename);
        formData.append('filename', filename);
        formData.append('chunkIndex', i);
        formData.append('totalChunks', totalChunks);
        formData.append('chunkId', chunkId);
        formData.append('gallery_mode', 'false');

        try {
            const response = await fetch('/notes/upload_chunk', {
                method: 'POST',
                headers: { 'X-CSRF-Token': csrfToken },
                body: formData
            });
            let result;
            const responseClone = response.clone();
            try {
                result = await response.json();
            } catch (e) {
                const errorText = await responseClone.text();
                console.error(`Non-JSON response for ${filename}:`, errorText);
                alert(`服务器响应无效: ${filename}，错误: ${errorText || '未知错误'}`);
                progressContainer.style.display = 'none';
                return;
            }
            if (!result.success) {
                console.error(`Upload failed for ${filename}: ${result.error}`);
                alert(`上传失败: ${result.error || '未知错误'} (文件: ${filename})`);
                progressContainer.style.display = 'none';
                return;
            }
            const progress = Math.round(((i + 1) / totalChunks) * 100);
            progressBar.style.width = `${progress}%`;
            progressText.textContent = `${progress}%`;
            if (i === totalChunks - 1 && result.note) {
                addNoteToDisplay(result.note);
                if (notesDisplay) notesDisplay.scrollTop = notesDisplay.scrollHeight;
            }
        } catch (error) {
            console.error(`Error uploading chunk for ${filename}:`, error);
            alert(`上传分片时出错: ${error.message} (文件: ${filename})`);
            progressContainer.style.display = 'none';
            return;
        }
    }
    progressContainer.style.display = 'none';
}

// --- 上传多个文件 ---
async function uploadMultipleFiles(files, mode) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressContainer = document.getElementById('uploadProgress');
    if (!progressBar || !progressText || !progressContainer) return;

    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';
    progressText.textContent = '0%';

    const totalFiles = files.length;
    let uploadedFiles = 0;
    const filePaths = [];

    for (const file of files) {
        const chunkSize = CHUNK_SIZE;
        const totalChunks = Math.ceil(file.size / chunkSize);
        const chunkId = `chunk-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const filename = file.name.toLowerCase();
        console.log(`File selected: ${filename}`);

        for (let i = 0; i < totalChunks; i++) {
            const start = i * chunkSize;
            const end = Math.min(start + chunkSize, file.size);
            const chunk = file.slice(start, end);
            const formData = new FormData();
            formData.append('chunk', chunk, filename);
            formData.append('filename', filename);
            formData.append('chunkIndex', i);
            formData.append('totalChunks', totalChunks);
            formData.append('chunkId', chunkId);
            formData.append('gallery_mode', mode === 'gallery' ? 'true' : 'false');

            try {
                const response = await fetch('/notes/upload_chunk', {
                    method: 'POST',
                    headers: { 'X-CSRF-Token': csrfToken },
                    body: formData
                });
                let result;
                const responseClone = response.clone();
                try {
                    result = await response.json();
                } catch (e) {
                    const errorText = await responseClone.text();
                    console.error(`Non-JSON response for ${filename}:`, errorText);
                    alert(`服务器响应无效: ${filename}，错误: ${errorText || '未知错误'}`);
                    progressContainer.style.display = 'none';
                    return;
                }
                if (!result.success) {
                    console.error(`Upload failed for ${filename}: ${result.error}`);
                    alert(`上传失败: ${result.error || '未知错误'} (文件: ${filename})`);
                    progressContainer.style.display = 'none';
                    return;
                }
                if (mode === 'gallery' && i === totalChunks - 1 && result.content) {
                    filePaths.push(result.content);
                } else if (i === totalChunks - 1 && result.note && mode !== 'gallery') {
                    filePaths.push(result.note.content);
                }
            } catch (error) {
                console.error(`Error uploading chunk for ${filename}:`, error);
                alert(`上传分片时出错: ${error.message} (文件: ${filename})`);
                progressContainer.style.display = 'none';
                return;
            }
        }
        uploadedFiles++;
        const progress = Math.round((uploadedFiles / totalFiles) * 100);
        progressBar.style.width = `${progress}%`;
        progressText.textContent = `${progress}%`;
    }

    try {
        const response = await fetch('/notes/add_multiple', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify({ mode: mode, file_paths: filePaths })
        });
        let result;
        const responseClone = response.clone();
        try {
            result = await response.json();
        } catch (e) {
            const errorText = await responseClone.text();
            console.error('Non-JSON response:', errorText);
            alert(`服务器响应无效: ${errorText || '未知错误'}`);
            progressContainer.style.display = 'none';
            return;
        }
        if (result.redirect) {
            alert(result.error || '会话已超时，请重新登录');
            window.location.href = result.redirect;
            return;
        }
        if (result.success && result.note) {
            addNoteToDisplay(result.note);
            if (notesDisplay) notesDisplay.scrollTop = notesDisplay.scrollHeight;
        } else {
            alert(`保存笔记失败: ${result.error || '未知错误'}`);
        }
    } catch (error) {
        console.error('Error saving multiple files:', error);
        alert(`保存多文件笔记时出错: ${error.message}`);
    }
    progressContainer.style.display = 'none';
}

// --- 发送笔记数据 ---
async function sendNoteData(type, content, filename) {
    const data = { type, content };
    if (filename) data.filename = filename;
    try {
        const response = await fetch('/notes/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (result.success && result.note) {
            addNoteToDisplay(result.note);
            if (notesDisplay) notesDisplay.scrollTop = notesDisplay.scrollHeight;
        } else {
            alert('添加笔记失败: ' + (result.error || '未知错误'));
        }
    } catch (error) {
        console.error('Error adding note:', error);
        alert('添加笔记时出错: ' + error.message);
    }
}

// --- 添加笔记到显示 ---
function addNoteToDisplay(note) {
    if (!notesDisplay) return;

    const noteDiv = document.createElement('div');
    noteDiv.className = 'note-entry';
    noteDiv.id = `note-${note.id}`;
    noteDiv.dataset.noteId = note.id;
    const timeSpan = document.createElement('span');
    timeSpan.className = 'timestamp';
    try {
        timeSpan.textContent = new Date(note.timestamp).toLocaleString() + ' UTC';
    } catch(e) {
        timeSpan.textContent = note.timestamp + ' UTC';
    }
    if (note.type === 'image' || note.type === 'file' || note.type === 'gallery' || note.type === 'zip') {
        if (note.md5) {
            const md5Span = document.createElement('span');
            md5Span.className = 'file-md5';
            md5Span.textContent = `MD5: ${note.md5}`;
            timeSpan.appendChild(md5Span);
        }
        if (note.file_size) {
            const sizeSpan = document.createElement('span');
            sizeSpan.className = 'file-size';
            sizeSpan.textContent = `(${formatFileSize(note.file_size)})`;
            timeSpan.appendChild(sizeSpan);
        }
    }
    noteDiv.appendChild(timeSpan);
    const contentDiv = document.createElement('div');
    contentDiv.className = 'note-content';
    noteDiv.appendChild(contentDiv);
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'note-actions';
    noteDiv.appendChild(actionsDiv);
    if (note.type === 'text') {
        const p = document.createElement('p');
        p.className = 'note-text';
        p.setAttribute('data-raw-text', note.content);
        p.innerHTML = convertUrlsToLinks(note.content);
        contentDiv.appendChild(p);
        actionsDiv.innerHTML = `
            <button class="btn-edit" title="编辑">✎</button>
            <button class="btn-save" title="保存" style="display: none;">✔</button>
            <button class="btn-cancel" title="取消" style="display: none;">✖</button>
            <button class="btn-delete" title="删除">🗑</button>`;
    } else if (note.type === 'image') {
        const img = document.createElement('img');
        img.src = note.content;
        img.alt = '笔记图片';
        img.dataset.fullSrc = note.content;
        contentDiv.appendChild(img);
        actionsDiv.innerHTML = `<button class="btn-delete" title="删除">🗑</button>`;
    } else if (note.type === 'file' || note.type === 'zip') {
        const a = document.createElement('a');
        a.href = note.content;
        a.textContent = note.raw_content || '下载文件';
        a.target = '_blank';
        contentDiv.appendChild(a);
        actionsDiv.innerHTML = `<button class="btn-delete" title="删除">🗑</button>`;
    } else if (note.type === 'gallery') {
        let images = note.content || [];
        if (!Array.isArray(images)) images = [images];
        images = images.filter(img => typeof img === 'string' && img.startsWith('/uploads/'));
        const galleryContainer = document.createElement('div');
        galleryContainer.className = 'gallery-container';
        galleryContainer.setAttribute('data-images', JSON.stringify(images));
        galleryContainer.dataset.currentPage = '0';
        galleryContainer.innerHTML = `
            <button class="gallery-arrow arrow-left" style="display: none;">←</button>
            <div class="gallery">
                ${images.map((img, index) => `<img src="${img || ''}" alt="画廊图片" data-full-src="${img || ''}" loading="lazy" style="${index >= 3 ? 'display: none;' : ''}">`).join('')}
            </div>
            <button class="gallery-arrow arrow-right" style="${images.length <= 3 ? 'display: none;' : ''}">→</button>
        `;
        contentDiv.appendChild(galleryContainer);
        actionsDiv.innerHTML = `<button class="btn-delete" title="删除">🗑</button>`;
        initializeGalleries(); // 确保新添加的画廊初始化
    }
    notesDisplay.appendChild(noteDiv);
}

// --- 格式化文件大小 ---
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    else if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    else return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
}

// --- 转换 URL 为链接 ---
function convertUrlsToLinks(text) {
    const urlPattern = /(https?:\/\/[^\s<]+[^<.,:;"')\]\s])/g;
    return text.replace(urlPattern, '<a href="$1" target="_blank">$1</a>').replace(/\n/g, '<br>');
}

// --- 编辑和删除逻辑 ---
if (notesDisplay) {
    notesDisplay.addEventListener('click', async (event) => {
        const target = event.target;
        const noteDiv = target.closest('.note-entry');
        if (!noteDiv) return;
        const noteId = noteDiv.dataset.noteId;

        if (target.classList.contains('btn-edit')) {
            if (currentEditingNote && currentEditingNote !== noteDiv) {
                alert('请先保存或取消当前编辑的笔记！');
                return;
            }
            if (noteDiv.classList.contains('editing')) return;
            noteDiv.classList.add('editing');
            currentEditingNote = noteDiv;
            const p = noteDiv.querySelector('.note-text');
            const rawText = p.dataset.rawText;
            const textarea = document.createElement('textarea');
            textarea.value = rawText;
            p.after(textarea);
            textarea.focus();
            noteDiv.querySelector('.btn-save').style.display = 'inline-block';
            noteDiv.querySelector('.btn-cancel').style.display = 'inline-block';
            noteDiv.querySelector('.btn-edit').style.display = 'none';
            noteDiv.querySelector('.btn-delete').style.display = 'none';
        } else if (target.classList.contains('btn-save')) {
            const textarea = noteDiv.querySelector('textarea');
            const newContent = textarea.value.trim();
            if (!newContent) {
                alert('内容不能为空');
                return;
            }
            try {
                const response = await fetch(`/notes/edit/${noteId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                    body: JSON.stringify({ content: newContent })
                });
                const result = await response.json();
                if (result.success) {
                    const p = noteDiv.querySelector('.note-text');
                    p.textContent = newContent;
                    p.dataset.rawText = newContent;
                    p.innerHTML = convertUrlsToLinks(newContent);
                    noteDiv.querySelector('.timestamp').textContent = new Date(result.new_timestamp).toLocaleString() + ' UTC';
                    noteDiv.classList.remove('editing');
                    textarea.remove();
                    noteDiv.querySelector('.btn-save').style.display = 'none';
                    noteDiv.querySelector('.btn-cancel').style.display = 'none';
                    noteDiv.querySelector('.btn-edit').style.display = 'inline-block';
                    noteDiv.querySelector('.btn-delete').style.display = 'inline-block';
                    currentEditingNote = null;
                } else {
                    alert('编辑失败: ' + (result.error || '未知错误'));
                }
            } catch (error) {
                console.error('Error editing note:', error);
                alert('编辑笔记时出错: ' + error.message);
            }
        } else if (target.classList.contains('btn-cancel')) {
            noteDiv.classList.remove('editing');
            noteDiv.querySelector('textarea').remove();
            noteDiv.querySelector('.btn-save').style.display = 'none';
            noteDiv.querySelector('.btn-cancel').style.display = 'none';
            noteDiv.querySelector('.btn-edit').style.display = 'inline-block';
            noteDiv.querySelector('.btn-delete').style.display = 'inline-block';
            currentEditingNote = null;
        } else if (target.classList.contains('btn-delete')) {
            if (!confirm('确定删除此笔记？')) return;
            try {
                const response = await fetch(`/notes/delete/${noteId}`, {
                    method: 'POST',
                    headers: { 'X-CSRF-Token': csrfToken }
                });
                const result = await response.json();
                if (result.success) {
                    noteDiv.remove();
                    if (!notesDisplay.querySelector('.note-entry')) {
                        notesDisplay.innerHTML = '<div class="no-notes">暂无笔记，请添加新笔记！</div>';
                    }
                } else {
                    alert('删除失败: ' + (result.error || '未知错误'));
                }
            } catch (error) {
                console.error('Error deleting note:', error);
                alert('删除笔记时出错: ' + error.message);
            }
        }
    });
}

// --- Ctrl+S 快捷键保存 ---
document.addEventListener('keydown', (event) => {
    if (event.ctrlKey && event.key === 's') {
        event.preventDefault();
        const editingNote = document.querySelector('.note-entry.editing');
        if (editingNote) {
            const saveButton = editingNote.querySelector('.btn-save');
            if (saveButton && saveButton.style.display !== 'none') saveButton.click();
        }
    }
});