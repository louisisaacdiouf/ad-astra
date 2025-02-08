use actix_web::{web, App, HttpResponse, HttpServer, Responder};
use serde::Deserialize;

#[derive(Deserialize)]
struct PdfRequest {
    file_path: String,
}

async fn extract_pdf_text(pdf_req: web::Json<PdfRequest>) -> impl Responder {
    // Récupération du chemin du fichier depuis la requête JSON
    let file_path = &pdf_req.file_path;

    // Lecture du fichier PDF
    let bytes = match std::fs::read(file_path) {
        Ok(b) => b,
        Err(e) => return HttpResponse::InternalServerError().body(format!("Erreur lors de la lecture du fichier : {}", e)),
    };

    // Extraction du texte à partir des octets du PDF
    let text = match pdf_extract::extract_text_from_mem(&bytes) {
        Ok(txt) => txt,
        Err(e) => return HttpResponse::InternalServerError().body(format!("Erreur lors de l'extraction du texte : {}", e)),
    };

    // Retourne le texte extrait sous forme de JSON
    HttpResponse::Ok().json(serde_json::json!({ "text": text }))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new()
            // Route POST /extract pour traiter l'extraction
            .route("/extract", web::post().to(extract_pdf_text))
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}
