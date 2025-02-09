use actix_cors::Cors;
use actix_web::{ http, web, App, HttpResponse, HttpServer, Responder };
use dotenv::dotenv;
use serde::Deserialize;
use std::env;

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
        Err(e) => {
            return HttpResponse::InternalServerError().body(
                format!("Erreur lors de la lecture du fichier : {}", e)
            );
        }
    };

    // Extraction du texte à partir des octets du PDF
    let text = match pdf_extract::extract_text_from_mem(&bytes) {
        Ok(txt) => txt,
        Err(e) => {
            return HttpResponse::InternalServerError().body(
                format!("Erreur lors de l'extraction du texte : {}", e)
            );
        }
    };

    // Retourne le texte extrait sous forme de JSON
    HttpResponse::Ok().json(serde_json::json!({ "text": text }))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Charger les variables d'environnement depuis le fichier .env
    dotenv().ok();

    // Récupérer l'adresse du serveur depuis la variable d'environnement SERVER_ADDR
    let server_addr = env
        ::var("EXTRACTION_SERVICE_ADDR")
        .unwrap_or_else(|_| "127.0.0.1:8081".to_string());

    println!("--------------------------------------------------");
    println!("                    EXTRACTION                    ");
    println!("--------------------------------------------------");
    println!("Serveur d'extraction écoute sur {}", server_addr);

    HttpServer::new(|| {
        App::new()
            .wrap(
                Cors::default()
                    .allowed_origin("http://127.0.0.1:8080")
                    .allowed_methods(vec!["GET", "POST"])
                    .allowed_headers(vec![http::header::CONTENT_TYPE])
                    .supports_credentials()
                    .max_age(3600)
            )
            // Route POST /extract pour traiter l'extraction
            .route("/extract", web::post().to(extract_pdf_text))
    })
        .bind(&server_addr)?
        .run().await
}
