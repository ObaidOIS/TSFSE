/**
 * CSS Module Type Declarations
 * 
 * Allows TypeScript to import CSS files without errors.
 */

declare module '*.css' {
  const content: { [className: string]: string };
  export default content;
}
