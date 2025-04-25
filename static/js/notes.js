class NotesApp {
    constructor() {
        this.csrfToken = document.querySelector('meta[name="csrf-token"]').content;
        this.currentPage = 1;
        this.initEventListeners();
        this.loadNotes();
        this.loadCategories();
        this.loadTags();
    }
    
    initEventListeners() {
        // 新建笔记按钮
        document.getElementById('newNoteBtn').addEventListener('click', () => {
            this.showNoteModal();
        });
        
        // 上传按钮
        document.getElementById('uploadBtn').addEventListener('click', () => {
            this.showUploadModal();
        });
        
        // 搜索输入
        document.getElementById('searchInput').addEventListener('input', (e) => {
            this.searchNotes(e.target.value);
        });
        
        // 保存笔记按钮
        document.getElementById('saveNoteBtn').addEventListener('click', () => {
            this.saveNote();
        });
        
        // 上传提交按钮
        document.getElementById('uploadSubmitBtn').addEventListener('click', () => {
            this.uploadFile();
        });
    }
    
    loadNotes(page = 1) {
        fetch(`/api/notes?page=${page}`)
            .then(response => response.json())
            .then(data => {
                this.renderNotes(data.notes);
                this.renderPagination(data);
                this.currentPage = page;
            });
    }
    
    renderNotes(notes) {
        const container = document.getElementById('notesContainer');
        container.innerHTML = '';
        
        if (notes.length === 0) {
            container.innerHTML = '<div class="alert alert-info">暂无笔记</div>';
            return;
        }
        
        notes.forEach(note => {
            const noteEl = this.createNoteElement(note);
            container.appendChild(noteEl);
        });
    }
    
    createNoteElement(note) {
        const noteEl = document.createElement('div');
        noteEl.className = 'note-card card mb-3';
        noteEl.dataset.noteId = note.id;
        
        let content = '';
        if (note.type === 'text') {
            content = `<div class="note-content">${note.content}</div>`;
        } else if (note.type === 'image') {
            content = `<div class="note-content"><img src="${note.url}" class="img-fluid"></div>`;
        } else {
            content = `<div class="note-content"><a href="${note.url}" target="_blank">${note.content}</a></div>`;
        }
        
        noteEl.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <small class="text-muted">${new Date(note.timestamp).toLocaleString()}</small>
                    <div>
                        <button class="btn btn-sm btn-outline-primary edit-btn me-1">编辑</button>
                        <button class="btn btn-sm btn-outline-danger delete-btn">删除</button>
                    </div>
                </div>
                ${content}
            </div>
        `;
        
        noteEl.querySelector('.edit-btn').addEventListener('click', () => {
            this.showNoteModal(note);
        });
        
        noteEl.querySelector('.delete-btn').addEventListener('click', () => {
            this.deleteNote(note.id);
        });
        
        return noteEl;
    }
    
    renderPagination(data) {
        const pagination = document.getElementById('pagination');
        pagination.innerHTML = '';
        
        if (data.pages <= 1) return;
        
        const ul = document.createElement('ul');
        ul.className = 'pagination justify-content-center';
        
        if (data.has_prev) {
            ul.appendChild(this.createPageItem('上一页', data.page - 1));
        }
        
        for (let i = 1; i <= data.pages; i++) {
            ul.appendChild(this.createPageItem(i, i, i === data.page));
        }
        
        if (data.has_next) {
            ul.appendChild(this.createPageItem('下一页', data.page + 1));
        }
        
        pagination.appendChild(ul);
    }
    
    createPageItem(text, page, active = false) {
        const li = document.createElement('li');
        li.className = `page-item ${active ? 'active' : ''}`;
        
        const a = document.createElement('a');
        a.className = 'page-link';
        a.href = '#';
        a.textContent = text;
        a.addEventListener('click', (e) => {
            e.preventDefault();
            this.loadNotes(page);
        });
        
        li.appendChild(a);
        return li;
    }
    
    showNoteModal(note = null) {
        const modal = new bootstrap.Modal(document.getElementById('noteModal'));
        const title = document.getElementById('modalTitle');
        const noteId = document.getElementById('noteId');
        const noteTitle = document.getElementById('noteTitle');
        const noteContent = document.getElementById('noteContent');
        
        if (note) {
            title.textContent = '编辑笔记';
            noteId.value = note.id;
            noteTitle.value = note.title || '';
            noteContent.value = note.content || '';
        } else {
            title.textContent = '新建笔记';
            noteId.value = '';
            noteTitle.value = '';
            noteContent.value = '';
        }
        
        modal.show();
    }
    
    saveNote() {
        const noteId = document.getElementById('noteId').value;
        const title = document.getElementById('noteTitle').value;
        const content = document.getElementById('noteContent').value;
        
        const url = noteId ? `/api/notes/${noteId}` : '/api/notes';
        const method = noteId ? 'PUT' : 'POST';
        
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': this.csrfToken
            },
            body: JSON.stringify({
                title: title,
                content: content
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('noteModal')).hide();
                this.loadNotes(this.currentPage);
            }
        });
    }
    
    deleteNote