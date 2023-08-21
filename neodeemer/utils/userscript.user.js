// ==UserScript==
// @name            Neodeemer UserScript
// @namespace       https://github.com/Tutislav/neodeemer
// @version         0.1
// @description     Script to add music to download queue from browser
// @icon            https://github.com/Tutislav/neodeemer/raw/main/neodeemer/data/icon.png
// @grant           GM_xmlhttpRequest
// @author          Tutislav
// @match           https://www.youtube.com/watch?v=*
// @match           https://www.youtube.com/playlist?list=*
// @connect         localhost
// @updateURL       https://raw.githubusercontent.com/Tutislav/neodeemer/main/neodeemer/utils/userscript.user.js
// @downloadURL     https://raw.githubusercontent.com/Tutislav/neodeemer/main/neodeemer/utils/userscript.user.js
// @supportURL      https://github.com/Tutislav/neodeemer/issues
// ==/UserScript==

(function () {
    'use strict';

    const host = "localhost";

    const downloadButtonCode = `<button id='neodeemer-download'
        style='background-color: transparent; border: 2px solid transparent; border-radius: 32px; cursor: pointer; float: right; font-size: 0; padding: 0; transition: border 0.5s;'
        onMouseOver='this.style.filter="brightness(1.25)"' onMouseOut='this.style.filter=""'>
        <img src='https://github.com/Tutislav/neodeemer/raw/main/neodeemer/data/icon.png' width='32'></button>`;

    var resetBorder = function () {
        var downloadButton = document.querySelector("#neodeemer-download");
        downloadButton.style.border = "2px solid transparent";
    };

    var addButton = function () {
        var downloadElement = document.querySelector("ytd-download-button-renderer");
        if (downloadElement) {
            downloadElement.setAttribute("is-hidden", "true");
        }
        var itemsDiv = document.querySelector("#middle-row");
        if (!itemsDiv) {
            itemsDiv = document.querySelector(".metadata-wrapper .description");
        }
        if (itemsDiv) {
            itemsDiv.removeAttribute("is-hidden");
            itemsDiv.innerHTML = itemsDiv.innerHTML + downloadButtonCode;
            var downloadButton = document.querySelector("#neodeemer-download");
        }
        if (itemsDiv && downloadButton) {
            downloadButton.onclick = function () {
                var url = "http://" + host + ":8686/download/" + window.location.href;
                GM_xmlhttpRequest({
                    method: "GET",
                    url: url,
                    onerror: function () {
                        downloadButton.style.border = "2px solid red";
                        setTimeout(resetBorder, 5000);
                    },
                    onload: function (response) {
                        if (response.status == 200) {
                            downloadButton.style.border = "2px solid lime";
                        }
                        else {
                            downloadButton.style.border = "2px solid red";
                        }
                        setTimeout(resetBorder, 5000);
                    }
                });
            };
        } else {
            setTimeout(addButton, 250);
        }
    };

    addButton();
})();