window.djq = window.djq || {};

function uploadQuillImage(file) {
    return fetch('/api/files/images', {
        method: 'POST',
        body: file,
        headers: {
            'Content-Disposition': 'attachement; filename="' + file.name + '"'
        }
    }).then(function (response) {
        return response.json();
    }).then(function (data) {
        return data.links.cover;
    });
}

function buildQuillConfig(config) {
    config.modules = config.modules || {};
    config.modules.imageUploader = {upload: uploadQuillImage};
    Quill.register({'modules/imageUploader': ImageUploader}, true);
    return config;
}

function applyInitialContent(wrapper, editor, input) {
    var delta = editor.getAttribute('data-delta');
    var html = editor.getAttribute('data-html');

    if (delta) {
        wrapper.quill.setContents(JSON.parse(delta));
        return;
    }
    if (html) {
        wrapper.quill.clipboard.dangerouslyPasteHTML(0, html);
        return;
    }
    if (!input.value) {
        return;
    }
    try {
        var stored = JSON.parse(input.value);
        wrapper.quill.setContents(JSON.parse(stored.delta));
    } catch (e) {
        wrapper.quill.clipboard.dangerouslyPasteHTML(0, input.value);
    }
}

function syncQuillInput(wrapper) {
    if (!wrapper || !wrapper.quill || !wrapper.targetInput || !wrapper.targetDiv) {
        return;
    }
    var editorHtml = wrapper.targetDiv.getElementsByClassName('ql-editor')[0].innerHTML;
    wrapper.targetInput.value = JSON.stringify({
        delta: JSON.stringify(wrapper.quill.getContents()),
        html: editorHtml
    });
}

function initBluebottleQuill(fieldId) {
    var editor = document.getElementById('quill-' + fieldId);
    var input = document.getElementById('quill-input-' + fieldId);

    if (!editor || !input) {
        return null;
    }
    if (fieldId.indexOf('__prefix__') !== -1 || editor.closest('.empty-form')) {
        return null;
    }
    if (editor.classList.contains('ql-container') || window.djq[fieldId]) {
        return window.djq[fieldId] || null;
    }

    var wrapper = new QuillWrapper(
        editor.id,
        input.id,
        buildQuillConfig(JSON.parse(editor.getAttribute('data-config')))
    );
    applyInitialContent(wrapper, editor, input);
    syncQuillInput(wrapper);
    window.djq[fieldId] = wrapper;
    return wrapper;
}

function initQuillWidgets(root) {
    if (!root || !root.querySelectorAll) {
        return;
    }
    root.querySelectorAll('.django-quill-widget[data-type="django-quill"]').forEach(function (editor) {
        initBluebottleQuill(editor.id.replace(/^quill-/, ''));
    });
}

document.addEventListener('formset:added', function (event) {
    initQuillWidgets(event.target);
});

if (window.django && django.jQuery) {
    django.jQuery(document).on('inline-group-row:added', function (event, $row) {
        initQuillWidgets($row && $row[0]);
    });
}

document.addEventListener('submit', function () {
    Object.keys(window.djq).forEach(function (fieldId) {
        syncQuillInput(window.djq[fieldId]);
    });
}, true);

window.initBluebottleQuill = initBluebottleQuill;
