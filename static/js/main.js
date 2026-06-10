function openRenameModal(type, id, currentName) {
    const modal = document.getElementById('renameModal');
    document.getElementById('renameType').value = type;
    document.getElementById('renameId').value = id;
    document.getElementById('renameName').value = currentName;
    modal.style.display = 'flex';
}

function openDeleteModal(type, id) {
    const modal = document.getElementById('deleteModal');
    document.getElementById('deleteType').value = type;
    document.getElementById('deleteId').value = id;
    modal.style.display = 'flex';
}

function openFolderModal() {
    document.getElementById('folderModal').style.display = 'flex';
}

function closeModals() {
    document.querySelectorAll('.modal').forEach(m => m.style.display = 'none');
}

// Close on outside click
window.onclick = function (event) {
    if (event.target.classList.contains('modal')) {
        closeModals();
        // Stop video if playing
        const video = document.getElementById('videoPlayer');
        if (video) video.pause();
    }
}

function openVideo(url, title) {
    const modal = document.getElementById('videoModal');
    const video = document.getElementById('videoPlayer');
    document.getElementById('videoTitle').textContent = title;
    video.src = url;
    modal.style.display = 'flex';
    video.play().catch(e => console.log('Auto-play prevent or error', e));
}

function openImage(url, title) {
    const modal = document.getElementById('imageModal');
    const img = document.getElementById('imageViewer');
    img.src = url;
    modal.style.display = 'flex';
}

// Ensure closing modals stops video
const originalClose = closeModals;
closeModals = function () {
    const video = document.getElementById('videoPlayer');
    if (video) {
        video.pause();
        video.src = "";
    }
    document.querySelectorAll('.modal').forEach(m => m.style.display = 'none');
}
