use std::time::Instant;

fn main() {
    let start = Instant::now();
    let bytes = std::fs::read("livre.pdf").unwrap();
    let out = pdf_extract::extract_text_from_mem(&bytes).unwrap();
    println!("{out}");
    println!("\n\nDuration: {:?}", start.elapsed());
}
