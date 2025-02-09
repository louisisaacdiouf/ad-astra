// Elements
let preloaderTxt = document.querySelector("#preloader h1");
let preloaderSubtitle = document.querySelector("#preloader-subtitle");
let uploadContainer = document.querySelector("#upload-container");
let uploadBtn = document.querySelector("#upload-btn");
let fileInput = document.querySelector("#file-input");
// let uploadOk = document.querySelector("#upload-ok");
let uploadForm = document.querySelector("#upload-form");
let anonymousImg = document.querySelector("#anonymous-img");
let actionsZone = document.querySelector("#actions-zone");
let uploadFormCloseDuration = 1300;
let terminalOpenDuration = 1300;
let anonymizationFormContent = `<form id="anonymization-form">
    <fieldset>
        <legend>Sélectionnez les types de données à anonymiser :</legend>
        <div>
            <input type="checkbox" id="person" name="data_types" value="PERSON">
            <label for="person">Personnes</label>
        </div>
        <div>
            <input type="checkbox" id="email" name="data_types" value="EMAIL">
            <label for="email">Emails</label>
        </div>
        <div>
            <input type="checkbox" id="phone" name="data_types" value="PHONE">
            <label for="phone">Numéros de téléphone</label>
        </div>
        <div>
            <input type="checkbox" id="address" name="data_types" value="ADDRESS">
            <label for="address">Adresses</label>
        </div>
        <!-- Ajoutez d'autres types de données selon vos besoins -->
    </fieldset>
    <button id="anonymizationOk" type="submit" class="text-black font-bold cursor-pointer">Anonymiser</button>
</form>`;


window.onload = async () => {

    // First animation
    LettersAnimation("#preloader h1", 0, undefined, false);
    LettersAnimation("#copyright", 0, undefined, false);
    await typing(preloaderSubtitle, "Anonymize your documents for free", "preloader", 20);

    // Next animations
    LettersAnimation("#preloader h1", 5000, undefined, true);
    LettersAnimation("#copyright", 5000, undefined, true);

    uploadBtn.addEventListener("click", () => {
        fileInput.click();
    });

    fileInput.addEventListener("change", () => {
        uploadForm.classList.remove("hidden");
    });

    /*---------------------------------------------
        Handle upload form submit
    ---------------------------------------------*/
    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        await new Promise(async (resolve) => {
            const fileInput = document.getElementById("file-input");
            const file = fileInput.files[0];
            if (!file) {
                return;
            }

            // Créer un FormData et y ajouter le fichier sous la clé "file"
            const formData = new FormData();
            formData.append("file", file);

            try {
                const uploadResponse = await fetch("/loadfile", {
                    method: "POST",
                    body: formData
                });
                if (!uploadResponse.ok) {
                    const errMsg = await uploadResponse.text();
                    throw new Error(`Erreur lors de l'upload: ${errMsg}`);
                }
                const uploadData = await uploadResponse.json();
                const filePath = uploadData.filepath;  // chemin du fichier uploadé
        
                // Vous pouvez ensuite lancer l'analyse sur ce fichier
                const groups = await analyzeDocument(filePath);
                if (groups) {
                    console.log("Groupes d'informations détectés:", groups);
                    let listGroups = "These are the groups of informations found in your document.\n";
                    groups.forEach(el=>{
                        listGroups += " [" + el.label + "]: " + el.meaning + ",     ";
                    });

                    anonymousImg.style.height = "10vh";
                    preloaderTxt.style.fontSize = "1.8em";
                    preloaderSubtitle.style.fontSize = "0.7em";
                    
                    // Définir la hauteur explicite à partir de la hauteur calculée de l'élément
                    uploadContainer.style.height = uploadContainer.scrollHeight + "px";
                
                    // Permettre au navigateur de rendre la modification
                    requestAnimationFrame(() => {
                        // Utiliser un setTimeout pour s'assurer que le changement de hauteur est bien pris en compte
                        setTimeout(() => {
                            uploadContainer.style.height = "0px";
                        }, 0);
                    });
                    
                    // Optionnel: Attendre la fin de la transition (ici 3000ms d'après ton CSS)
                    await new Promise((resolve) => {
                        setTimeout(() =>{
                            uploadContainer.remove();
                            resolve();
                        }, uploadFormCloseDuration);
                    });

                    /*---------------------------------------------
                        Start actions
                    ---------------------------------------------*/

                    // Labélisation
                    let analyzeTerminal = new Terminal("analyze", listGroups);
                    await analyzeTerminal.load(actionsZone);
                    
                    // let p = document.querySelector(`#${analyzeTerminal.name}-text`)
                    // await typing(p, listGroups, analyzeTerminal.name, 15);

                    // Anonymisation
                    let anoText = "Générer une version anonymisée du document";
                    let anonymizationTerminal = new Terminal("anonymization", anoText);
                    await anonymizationTerminal.load(actionsZone);
                    
                    let pAnon = document.querySelector(`#${anonymizationTerminal.name}-text`);
                    // await typing(pAnon, anoText, anonymizationTerminal.name, 8);
                    pAnon.innerHTML += anonymizationFormContent;

                    // Ajout de l'écouteur d'événements pour le formulaire
                    const anonymizationForm = document.getElementById("anonymization-form");
                    anonymizationForm.addEventListener("submit", async (e) => {
                        e.preventDefault();

                        // Récupérer les types de données sélectionnées
                        const selectedTypes = Array
                        .from(document.querySelectorAll('input[name="data_types"]:checked'))
                        .map(input => input.value);

                        if (selectedTypes.length === 0) {
                            // alert("Veuillez sélectionner au moins un type de donnée à anonymiser.");
                            return;
                        }

                        try {
                            // Construire la charge utile pour l'anonymisation
                            const anonymizationPayload = {
                                file_path: filePath, // Assurez-vous que 'filePath' est bien accessible dans ce contexte
                                forbidden_labels: selectedTypes
                            };

                            console.log(JSON.stringify(anonymizationPayload));
                    
                            // Envoi de la requête d'anonymisation
                            const response = await fetch("http://127.0.0.1:8080/entry", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify(anonymizationPayload)
                            });
                    
                            if (!response.ok) {
                                const errMsg = await response.text();
                                throw new Error(`Erreur lors de l'anonymisation: ${errMsg}`);
                            }
                    
                            const result = await response.json();
                            let link = filePath.replace("temp", "output_dir").replace(".pdf", "_redacted.pdf");
                            console.log("Fichier anonymisé disponible à :", link);
                    
                            // Afficher un message de confirmation ou proposer le téléchargement
                            pAnon.innerHTML += `<br>Document anonymisé généré: <a href="${link}" target="_blank">Télécharger ici</a>`;
                        } catch (error) {
                            console.error("Erreur lors de l'anonymisation:", error);
                            alert("Une erreur est survenue lors de l'anonymisation.");
                        }
                    });
                }
            } catch (error) {
                console.error("Erreur lors de l'upload:", error);
                // Afficher une erreur à l'utilisateur selon vos besoins.
            }
            resolve();
        })
    });
}

class Terminal {
    constructor(name, txt) {
        [this.name, this.txt] = [name, txt];
        this.HTMLContent = makeTerminal(name, "p-"+name);
    }

    async load(parent) {
        // Load content
        parent.innerHTML += this.HTMLContent;
        this.HTMLElement = document.querySelector("#"+this.name);

        // Terminal Pop-up
        this.HTMLElement.style.overflow = "hidden";
        await new Promise((resolve) => {
            setTimeout(async () => {
                this.HTMLElement.style.opacity = "1";
                this.HTMLElement.style.height = "70vh";
                this.HTMLElement.style.width = "100%";
                resolve();
            }, 200)
        });

        // await waiting(terminalOpenDuration);

        this.p = this.HTMLElement.querySelector(`#${this.name}-text`);
        await typing(this.p, this.txt, this.name, 25);
    }
}

function makeTerminal (name, pClass) {
    return `
    <div id="${name}" class="terminal-box">
        <div class="terminal-head">&lt;${name.toUpperCase()}/&gt;</div>
        <div class="terminal-body">
            <p id="${name}-text" class="${pClass}"></p>
        </div>
    </div>`;
}

async function waiting(duration) {
    return new Promise((resolve) => setTimeout(resolve, terminalOpenDuration));
}

/**
 * Fonction qui demande au serveur d'extraction de renvoyer le contenu du PDF,
 * puis qui passe ce contenu au serveur de labellisation.
 * Enfin, elle groupe les entités par label et ajoute la signification de chaque label.
 * 
 * @param {string} filePath - Chemin du fichier PDF sur le serveur.
 * @returns {Promise<Array>} - Un tableau d'objets regroupant les entités par label.
 *                             Chaque objet contient : { label, meaning, values }.
 */
async function analyzeDocument(filePath) {
    try {
        // 1. Demande d'extraction du contenu
        const extractionPayload = { file_path: filePath };
        const extractionRes = await fetch("http://127.0.0.1:8081/extract", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(extractionPayload)
        });
        if (!extractionRes.ok) {
            const errMsg = await extractionRes.text();
            throw new Error("Erreur extraction: " + errMsg);
        }
        const extractionData = await extractionRes.json();
        // extractionData attendue : { text: "contenu extrait" }

        // 2. Demande de labellisation en passant le texte extrait
        const labellingPayload = { text: extractionData.text };
        const labellingRes = await fetch("http://127.0.0.1:8082/label", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(labellingPayload)
        });
        if (!labellingRes.ok) {
            const errMsg = await labellingRes.text();
            throw new Error("Erreur labelling: " + errMsg);
        }
        const labellingData = await labellingRes.json();
        // labellingData attendue : { extracted_text: "...", entities: [ { text: "Isaac", label: "PERSON" }, ... ] }

        // 3. Grouper les entités par label
        const groups = {};
        labellingData.entities.forEach(entity => {
            if (!groups[entity.label]) {
                groups[entity.label] = [];
            }
            groups[entity.label].push(entity.text);
        });

        // 4. Mapping des labels aux significations
        const labelMeanings = {
            "PERSON": "Personnes",
            "EMAIL": "Emails",
            "PHONE": "Numéros de téléphone",
            "ADDRESS": "Adresses",
            "CARD": "Numéros de carte",
            "GPE": "Entités géopolitiques",
            "ORG": "Organisations",
            "MISC": "Divers"
        };

        // 5. Construire la structure finale
        const finalGroups = [];
        for (const [label, values] of Object.entries(groups)) {
            finalGroups.push({
                label: label,
                meaning: labelMeanings[label] || label,
                values: values
            });
        }
        return finalGroups;
    } catch (error) {
        console.error("Erreur dans analyzeDocument:", error);
        return null;
    }
}