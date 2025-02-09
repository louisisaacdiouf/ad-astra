const speed = 80;

async function typeInTxts(selector, txtsList, className, s = speed) {
    let elementsList = document.querySelectorAll(`${selector} .txt`);

    for (let x = 0; x < txtsList.length; x++) {
        await typing(elementsList[x], txtsList[x].txt, className, s);
    }
}

function typing(element, txt, className, s = speed) {
    return new Promise(async (resolve) => {
        for (let i = 0; i < txt.length; i++) {
            await typeChar(s, element, txt, className, i);
        }
        resolve();
    });
}

function typeChar(delay, element, txt, className, i) {
    return new Promise((resolve) => {
        setTimeout(() => {
            let prevUnderscore = document.querySelector("#" + className + "-underscore");
            if (prevUnderscore) {
                prevUnderscore.remove();
            }
            element.innerHTML += txt.charAt(i);
            let newUnderscore = document.createElement("span");
            newUnderscore.textContent = "_";
            newUnderscore.id = className + "-underscore";
            newUnderscore.className = "cursor blinking";
            element.appendChild(newUnderscore);
            resolve();
        }, delay);
    });
}

function formToggle() {
    document.querySelectorAll("#register-btn,#login-btn").forEach(el => {
        el.addEventListener("click", async (e) => {
            if (!e.target.classList.contains("active")) {
                let authBox = document.querySelector("#" + activeForm);
                await new Promise((resolve) => {
                    authBox.classList.add("instant-slide-top");
                    resolve();
                })
                await new Promise((resolve) => {
                    setTimeout(async () => {
                        authBox.remove();
                        document.querySelector("#terminal-zone").innerHTML = activeForm === "login" ? registerTerminal : loginTerminal;
                        activeForm = activeForm === "login" ? "register" : "login";
                        document.querySelector("#" + activeForm).classList.remove("not-displayed");
                        e.target.classList.add("active")
                        otherBtn().classList.remove("active")
                        await startActiveTerminal(activeForm, txtDataToLoad());
                        fieldLoaded = false;
                        resolve();
                    }, 750);
                })
            }
        });
    });
}

function shrinkLeftBox() {
    return new Promise((resolve) => {
        let leftBox = document.querySelector("#auth-left")
        leftBox.style.width = "calc(50% - 2vh)";
        leftBox.style.marginLeft = "0";
        resolve();
    });
}

function btnBgPosition() {
    document.querySelectorAll(".btn-bg").forEach(el => {
        if (el.parentNode.id === "login-btn") {
            el.style.right = "0"
        } else {
            el.style.left = "0"
        }
    })
}

async function ShowAllPosts(posts) {
    let postsZone = document.createElement("div");
    postsZone.id = "posts-zone";

    posts.forEach((postData, i) => {
        // Post
        let post = document.createElement("div");
        post.className = "post";
        postImage = postData.PostPicture ? makePostImage(postData.image) : "";
        post.innerHTML = makePost(postData)
        postsZone.appendChild(post);
        setTimeout(() => {
            post.style.opacity = "1";
        }, 500 + i * 500);
    });

    document.querySelector("#all-posts .terminal-body").appendChild(postsZone);
}

function LettersAnimation(selector, interval = 5000, speed = 30, loop = true) {
    let alphabet = 'abcdefghijklmnopqrstuvwxyz';
    let randomLetter = () => alphabet[Math.floor(Math.random() * 26)];

    document.querySelectorAll(selector).forEach(el => {
        el.dataset.name = el.textContent;

        const repeat = setInterval(() => {
            let iter = 0;
            const interval = setInterval(() => {
                el.textContent = el.textContent
                    .split("")
                    .map((letter, i) => {
                        if (i < iter) {
                            return el.dataset.name[i];
                        }
                        return randomLetter();
                    })
                    .join("");

                if (iter >= el.dataset.name.length) clearInterval(interval)

                iter += 1 / 3;
            }, speed);

            if (!loop) clearInterval(repeat);
        }, interval);
    });
}

function terminalScrollBottom(selector) {
    let tlElement = document.querySelector(selector)
    if (tlElement) {
        let tl = tlElement.closest(".terminal-box");
        tl.scrollTop = tl.scrollHeight;
    }
}

function insertMsg(refElement, isOld, className, date, author, msg) {
    // Insert message
    let index = (arr) => isOld ? 0 : arr.length - 1;
    let status = isOld ? "old" : "new";

    refElement.before(makeSpan(`${className} ${status}-msg-name`));
    let name = document.querySelectorAll(`.${status}-msg-name`);

    name[index(name)].textContent = `[${formatDate(date)}][${author}]:`;
    name[index(name)].after(makeSpan(`${status}-msg-txt`));

    let txt = document.querySelectorAll(`.${status}-msg-txt`);
    txt[index(txt)].textContent = msg;

    txt[index(txt)].after(makeBr());
}